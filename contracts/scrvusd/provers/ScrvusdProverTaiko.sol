// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import "./ScrvusdProverBase.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface ISignalService {
    function getSyncedChainData(uint64 _chainId, bytes32 _kind, uint64 _blockId)
        external
        view
        returns (uint64 blockId_, bytes32 chainData_);
}

contract ScrvusdProverTaiko is ScrvusdProverBase {
    address public constant SIGNAL_SERVICE = 0x1670000000000000000000000000000000000005;
    bytes32 internal constant H_STATE_ROOT = keccak256("STATE_ROOT");

    constructor(address _scrvusd_oracle) ScrvusdProverBase(_scrvusd_oracle) {}

    /// @param _block_number The block number of known block
    /// @param _proof_rlp The state proof of the parameters.
    function prove(
        uint64 _block_number,
        bytes memory _proof_rlp
    ) external returns (uint256) {
        (uint64 blockId, bytes32 stateRoot) = ISignalService(SIGNAL_SERVICE).getSyncedChainData(
            1,
            H_STATE_ROOT,
            _block_number
        );

        uint256[PARAM_CNT] memory params = _extractParametersFromProof(stateRoot, _proof_rlp);

        // Use last_profit_update as the timestamp surrogate
        return _updatePrice(params, params[5]);
    }
}