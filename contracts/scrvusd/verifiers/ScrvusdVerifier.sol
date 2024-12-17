// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import "./ScrvusdVerifierBase.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.8/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
}

contract ScrvusdVerifier is ScrvusdVerifierBase {
    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _scrvusd_oracle)
        ScrvusdVerifierBase(_scrvusd_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
    }

    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the parameters
    function prove(
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
        return _updatePrice(params, block_header.timestamp);
    }
}