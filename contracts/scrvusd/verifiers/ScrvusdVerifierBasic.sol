// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import "./ScrvusdVerifierCore.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
    function get_state_root(uint256 _number) external view returns (bytes32);
}

contract ScrvusdVerifierBasic is ScrvusdVerifierCore {
    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _scrvusd_oracle)
        ScrvusdVerifierCore(_scrvusd_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
    }

    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function verifyScrvusdByBlockHash(
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external returns (uint256) {
        Verifier.BlockHeader memory block_header = Verifier.parseBlockHeader(_block_header_rlp);
        require(block_header.hash != bytes32(0), "Invalid blockhash");
        require(
            block_header.hash == IBlockHashOracle(BLOCK_HASH_ORACLE).get_block_hash(block_header.number),
            "Blockhash mismatch"
        );

        uint256[PARAM_CNT] memory params = _extractParametersFromProof(block_header.stateRootHash, _proof_rlp);
        return _updatePrice(params, block_header.timestamp, block_header.number);
    }

    /// @param _block_number Number of the block to use state root hash
    /// @param _proof_rlp The state proof of the parameters
    function verifyScrvusdByStateRoot(
        uint256 _block_number,
        bytes memory _proof_rlp
    ) external returns (uint256) {
        bytes32 state_root = IBlockHashOracle(BLOCK_HASH_ORACLE).get_state_root(_block_number);

        uint256[PARAM_CNT] memory params = _extractParametersFromProof(state_root, _proof_rlp);
        // Use last_profit_update as the timestamp surrogate
        return _updatePrice(params, params[5], _block_number);
    }
}