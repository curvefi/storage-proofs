// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import "./DelegationVerifierBase.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
}

contract DelegationVerifier is DelegationVerifierBase {
    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _vecrv_oracle)
        DelegationVerifierBase(_vecrv_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
    }

    /// @param _from Address from which balance is delegated
    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function verify(
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
}