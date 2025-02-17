// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
}

interface IScrvusdOracle {
    function update_price(
        uint256[2 + 5] memory _parameters,
        uint256 ts
    ) external returns (uint256);
}

/// @title Scrvusd Prover
/// @author Curve Finance
contract ScrvusdProver {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    address constant SCRVUSD =
        0x0655977FEb2f289A4aB78af67BAB0d17aAb84367;
    bytes32 constant SCRVUSD_HASH =
        keccak256(abi.encodePacked(SCRVUSD));

    address public immutable BLOCK_HASH_ORACLE;
    address public immutable SCRVUSD_ORACLE;

    uint256 constant PARAM_CNT = 2 + 5;
    uint256 constant PROOF_CNT = 1 + PARAM_CNT;  // account proof first

    constructor(address _block_hash_oracle, address _scrvusd_oracle) {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
        SCRVUSD_ORACLE = _scrvusd_oracle;
    }

    /// Prove parameters of scrvUSD rate.
    /// @param _block_header_rlp The block header of any block.
    /// @param _proof_rlp The state proof of the parameters.
    function prove(
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external returns (uint256) {
        Verifier.BlockHeader memory block_header = Verifier.parseBlockHeader(
            _block_header_rlp
        );
        require(block_header.hash != bytes32(0)); // dev: invalid blockhash
        require(
            block_header.hash ==
                IBlockHashOracle(BLOCK_HASH_ORACLE).get_block_hash(
                    block_header.number
                )
        ); // dev: blockhash mismatch

        // convert _proof_rlp into a list of `RLPItem`s
        RLPReader.RLPItem[] memory proofs = _proof_rlp.toRlpItem().toList();
        require(proofs.length == PROOF_CNT); // dev: invalid number of proofs

        // 0th proof is the account proof for the scrvUSD contract
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            SCRVUSD_HASH, // position of the account is the hash of its address
            block_header.stateRootHash,
            proofs[0].toList()
        );
        require(account.exists); // dev: scrvUSD account does not exist

        // iterate over proofs
        uint256[PROOF_CNT] memory PARAM_SLOTS = [
            uint256(0), // filler, account proof, no slot

            // Assets parameters
            21, // total_debt
            22, // total_idle

            // Supply parameters
            20, // totalSupply
            38, // full_profit_unlock_date
            39, // profit_unlocking_rate
            40, // last_profit_update
            uint256(keccak256(abi.encode(18, SCRVUSD))) // balance_of_self
        ];
        uint256[PARAM_CNT] memory params;
        Verifier.SlotValue memory slot;
        for (uint256 idx = 1; idx < PROOF_CNT; idx++) {
            slot = Verifier.extractSlotValueFromProof(
                keccak256(abi.encode(PARAM_SLOTS[idx])),
                account.storageRoot,
                proofs[idx].toList()
            );
            // Some slots may not be used => not exist, e.g. total_debt
            // require(slot.exists);

            params[idx - 1] = slot.value;
        }
        return IScrvusdOracle(SCRVUSD_ORACLE).update_price(params, block_header.timestamp);
    }
}
