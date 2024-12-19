// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

uint256 constant PARAM_CNT = 2 + 5;
uint256 constant PROOF_CNT = 1 + PARAM_CNT;

interface IScrvusdOracle {
    function update_price(
        uint256[PARAM_CNT] memory _parameters,
        uint256 ts
    ) external returns (uint256);
}

// @dev This contract provides shared logic implementations 
// to be inherited by chain-specific contracts.
abstract contract ScrvusdVerifierShared {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    // Common constants
    address private constant SCRVUSD = 0x0655977FEb2f289A4aB78af67BAB0d17aAb84367;
    bytes32 private constant SCRVUSD_HASH = keccak256(abi.encodePacked(SCRVUSD));

    // Storage slots of parameters
    uint256[PROOF_CNT] internal PARAM_SLOTS = [
        uint256(0), // filler for account proof
        uint256(21), // total_debt
        uint256(22), // total_idle
        uint256(20), // totalSupply
        uint256(38), // full_profit_unlock_date
        uint256(39), // profit_unlocking_rate
        uint256(40), // last_profit_update
        uint256(keccak256(abi.encode(18, SCRVUSD))) // balanceOf(self)
    ];

    address public immutable SCRVUSD_ORACLE;

    constructor(address _scrvusd_oracle) {
        SCRVUSD_ORACLE = _scrvusd_oracle;
    }

    /// @dev Extract parameters from the state proof using the given state root.
    function _extractParametersFromProof(
        bytes32 stateRoot,
        bytes memory proofRlp
    ) internal view returns (uint256[PARAM_CNT] memory) {
        RLPReader.RLPItem[] memory proofs = proofRlp.toRlpItem().toList();
        require(proofs.length == PROOF_CNT, "Invalid number of proofs");

        // Extract account proof
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            SCRVUSD_HASH,
            stateRoot,
            proofs[0].toList()
        );
        require(account.exists, "scrvUSD account does not exist");

        // Extract slot values
        uint256[PARAM_CNT] memory params;
        for (uint256 i = 1; i < PROOF_CNT; i++) {
            Verifier.SlotValue memory slot = Verifier.extractSlotValueFromProof(
                keccak256(abi.encode(PARAM_SLOTS[i])),
                account.storageRoot,
                proofs[i].toList()
            );
            // Slots might not exist, but typically we just read them.
            params[i - 1] = slot.value;
        }

        return params;
    }

    /// @dev Calls the oracle to update the price parameters.
    ///      Both child contracts use the same oracle call, differing only in how they obtain the timestamp.
    function _updatePrice(
        uint256[PARAM_CNT] memory params,
        uint256 ts
    ) internal returns (uint256) {
        return IScrvusdOracle(SCRVUSD_ORACLE).update_price(params, ts);
    }
}