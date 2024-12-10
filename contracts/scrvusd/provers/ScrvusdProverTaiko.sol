// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface ISignalService {
    function getSyncedChainData(uint64 _chainId, bytes32 _kind, uint64 _blockId)
        external view returns (uint64 blockId_, bytes32 chainData_);
}

interface IScrvusdOracle {
    function update_price(
        uint256[2 + 5] memory _parameters,
        uint256 ts
    ) external returns (uint256);
}

/// @title Scrvusd Prover
/// @author Curve Finance
contract ScrvusdProverTaiko {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    address constant SCRVUSD =
        0x0655977FEb2f289A4aB78af67BAB0d17aAb84367;
    bytes32 constant SCRVUSD_HASH =
        keccak256(abi.encodePacked(SCRVUSD));

    address public constant SIGNAL_SERVICE = 0x1670000000000000000000000000000000000005;
    address public immutable SCRVUSD_ORACLE;

    bytes32 internal constant H_STATE_ROOT = keccak256("STATE_ROOT");

    uint256 constant PARAM_CNT = 2 + 5;
    uint256 constant PROOF_CNT = 1 + PARAM_CNT;  // account proof first

    constructor(address _scrvusd_oracle) {
        SCRVUSD_ORACLE = _scrvusd_oracle;
    }

    /// Prove parameters of scrvUSD rate.
    /// @param _block_number The block number of known block
    /// @param _proof_rlp The state proof of the parameters.
    function prove(
        uint64 _block_number,
        bytes memory _proof_rlp
    ) external returns (uint256) {
        // convert _proof_rlp into a list of `RLPItem`s
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length == PROOF_CNT); // dev: invalid number of proofs

        // get state root hash
        uint64 blockId = 0;
        bytes32 stateRoot = 0;
        (blockId, stateRoot) = ISignalService(SIGNAL_SERVICE).getSyncedChainData(1, H_STATE_ROOT, _block_number);

        // 0th proof is the account proof for the scrvUSD contract
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            SCRVUSD_HASH, // position of the account is the hash of its address
            stateRoot, // State root hash
            proofs[0].toList()
        );
        require(account.exists); // dev: scrvUSD account does not exist

        // iterate over proofs
        uint256[PROOF_CNT] memory PARAM_SLOTS = [
            0,  // filler (account proof)

            // Assets parameters
            uint256(21),  // total_debt
            22,  // total_idle

            // Supply parameters
            20,  // totalSupply
            38,  // full_profit_unlock_date
            39,  // profit_unlocking_rate
            40,  // last_profit_update
            uint256(keccak256(abi.encode(18, SCRVUSD)))  // balance_of_self
        ];
        uint256[PARAM_CNT] memory params;
        Verifier.SlotValue memory slot;
        for (uint256 idx = 1; idx < PROOF_CNT; idx++) {
            slot = Verifier.extractSlotValueFromProof(
                keccak256(abi.encode(PARAM_SLOTS[idx])),
                account.storageRoot,
                proofs[idx].toList()
            );
            // Some slots may not be used => not exist, e.g. total_idle
            // require(slot.exists);

            params[idx - 1] = slot.value;
        }
        // block.timestamp not available, using `last_profit_update`
        return IScrvusdOracle(SCRVUSD_ORACLE).update_price(params, params[5]);
    }
}
