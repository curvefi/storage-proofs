// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
    function get_state_root(uint256 _number) external view returns (bytes32);
}

interface IVecrvOracle {
    function update_delegation(
        address from,
        address to,
        uint256 block_number
    ) external;
}

contract DelegationVerifier {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    address private constant VE_DELEGATE = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2;
    bytes32 private constant VE_DELEGATE_HASH = keccak256(abi.encodePacked(VE_DELEGATE));

    address public immutable VE_ORACLE;
    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _vecrv_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
        VE_ORACLE = _vecrv_oracle;
    }

    /// @param _from Address from which balance is delegated
    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function verifyDelegationByBlockHash(
        address _from,
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external {
        Verifier.BlockHeader memory block_header = Verifier.parseBlockHeader(_block_header_rlp);
        require(block_header.hash != bytes32(0), "Invalid blockhash");
        require(
            block_header.hash == IBlockHashOracle(BLOCK_HASH_ORACLE).get_block_hash(block_header.number),
            "Blockhash mismatch"
        );

        return _updateDelegation(_from, block_header.number, block_header.stateRootHash, _proof_rlp);
    }

    /// @param _from Address from which balance is delegated
    /// @param _block_number Number of the block to use state root hash
    /// @param _proof_rlp The state proof of the parameters
    function verifyDelegationByStateRoot(
        address _from,
        uint256 _block_number,
        bytes memory _proof_rlp
    ) external {
        bytes32 state_root = IBlockHashOracle(BLOCK_HASH_ORACLE).get_state_root(_block_number);

        return _updateDelegation(_from, _block_number, state_root, _proof_rlp);
    }

    /// @dev Update delegation using proof. `blockNumber` is used for updates linearization
    function _updateDelegation(
        address from,
        uint256 blockNumber,
        bytes32 stateRoot,
        bytes memory proofRlp
    ) internal {
        RLPReader.RLPItem[] memory proofs = proofRlp.toRlpItem().toList();
        require(proofs.length == 2, "Invalid number of proofs");

        // Extract account proof
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            VE_DELEGATE_HASH,
            stateRoot,
            proofs[0].toList()
        );
        require(account.exists, "Delegate account does not exist");

        // Extract slot values
        address to = address(uint160(Verifier.extractSlotValueFromProof(
            keccak256(abi.encode(
                keccak256(abi.encode(
                    keccak256(abi.encode(1, block.chainid)), // slot of delegation_from[chain.id][]
                    from
                ))
            )),
            account.storageRoot,
            proofs[1].toList()
        ).value));
        require(to != VE_DELEGATE, "Delegate not set");

        return IVecrvOracle(VE_ORACLE).update_delegation(from, to, blockNumber);
    }
}
