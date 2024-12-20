// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import "./VecrvVerifierCore.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
    function get_state_root(uint256 _number) external view returns (bytes32);
}

contract VecrvVerifier is VecrvVerifierCore {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _vecrv_oracle)
        VecrvVerifierCore(_vecrv_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
    }

    /// @param _user User to verify balance for
    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function verifyBalanceByBlockHash(
        address _user,
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external {
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length >= 1, "Invalid number of proofs");
        bytes32 storage_root = _extractAccountStorageRoot(_block_header_rlp, proofs[0]);

        _updateTotal(storage_root, proofs[1].toList());
        _updateBalance(_user, storage_root, proofs[2].toList());
    }

    /// @param _user User to verify balance for
    /// @param _block_number Number of the block to use state root hash
    /// @param _proof_rlp The state proof of the parameters
    function verifyBalanceByStateRoot(
        address _user,
        uint256 _block_number,
        bytes memory _proof_rlp
    ) external {
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length >= 1, "Invalid number of proofs");
        bytes32 state_root = IBlockHashOracle(BLOCK_HASH_ORACLE).get_state_root(_block_number);
        bytes32 storage_root = _extractAccountStorageRoot(state_root, proofs[0]);

        _updateTotal(storage_root, proofs[1].toList());
        _updateBalance(_user, storage_root, proofs[2].toList());
    }

    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function verifyTotalByBlockHash(
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external {
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length >= 1, "Invalid number of proofs");
        bytes32 storage_root = _extractAccountStorageRoot(_block_header_rlp, proofs[0]);

        _updateTotal(storage_root, proofs[1].toList());
    }

    /// @param _block_number Number of the block to use state root hash
    /// @param _proof_rlp The state proof of the parameters
    function verifyTotalByStateRoot(
        uint256 _block_number,
        bytes memory _proof_rlp
    ) external {
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length >= 1, "Invalid number of proofs");
        bytes32 state_root = IBlockHashOracle(BLOCK_HASH_ORACLE).get_state_root(_block_number);
        bytes32 storage_root = _extractAccountStorageRoot(state_root, proofs[0]);

        _updateTotal(storage_root, proofs[1].toList());
    }

    function _extractAccountStorageRoot(
        bytes memory _block_header_rlp,
        RLPReader.RLPItem memory account_proof
    ) internal returns (bytes32) {
        Verifier.BlockHeader memory block_header = Verifier.parseBlockHeader(_block_header_rlp);
        require(block_header.hash != bytes32(0), "Invalid blockhash");
        require(
            block_header.hash == IBlockHashOracle(BLOCK_HASH_ORACLE).get_block_hash(block_header.number),
            "Blockhash mismatch"
        );
        return _extractAccountStorageRoot(block_header.stateRootHash, account_proof);
    }
}