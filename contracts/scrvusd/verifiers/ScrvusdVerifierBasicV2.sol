// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {ScrvusdVerifierBasic, IBlockHashOracle, ScrvusdVerifierCore} from "./ScrvusdVerifierBasic.sol";
import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

interface IScrvusdOracleV2 {
    function update_profit_max_unlock_time(
        uint256 _profit_max_unlock_time,
        uint256 _block_number
    ) external returns (bool);
}

contract ScrvusdVerifierBasicV2 is ScrvusdVerifierBasic {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    uint256 internal PERIOD_SLOT = 37; // profit_max_unlock_time

    constructor(address _scrvusd, address _block_hash_oracle, address _scrvusd_oracle)
        ScrvusdVerifierBasic(_scrvusd, _block_hash_oracle, _scrvusd_oracle) {}

    /// @param _block_header_rlp The RLP-encoded block header
    /// @param _proof_rlp The state proof of the period
    function verifyPeriodByBlockHash(
        bytes memory _block_header_rlp,
        bytes memory _proof_rlp
    ) external returns (bool) {
        Verifier.BlockHeader memory block_header = Verifier.parseBlockHeader(_block_header_rlp);
        require(block_header.hash != bytes32(0), "Invalid blockhash");
        require(
            block_header.hash == IBlockHashOracle(ScrvusdVerifierBasic.BLOCK_HASH_ORACLE).get_block_hash(block_header.number),
            "Blockhash mismatch"
        );

        uint256 period = _extractPeriodFromProof(block_header.stateRootHash, _proof_rlp);
        return IScrvusdOracleV2(SCRVUSD_ORACLE).update_profit_max_unlock_time(period, block_header.number);
    }

    /// @param _block_number Number of the block to use state root hash
    /// @param _proof_rlp The state proof of the period
    function verifyPeriodByStateRoot(
        uint256 _block_number,
        bytes memory _proof_rlp
    ) external returns (bool) {
        bytes32 state_root = IBlockHashOracle(ScrvusdVerifierBasic.BLOCK_HASH_ORACLE).get_state_root(_block_number);

        uint256 period = _extractPeriodFromProof(state_root, _proof_rlp);
        return IScrvusdOracleV2(SCRVUSD_ORACLE).update_profit_max_unlock_time(period, _block_number);
    }

    /// @dev Extract period from the state proof using the given state root.
    function _extractPeriodFromProof(
        bytes32 stateRoot,
        bytes memory proofRlp
    ) internal view returns (uint256) {
        RLPReader.RLPItem[] memory proofs = proofRlp.toRlpItem().toList();
        require(proofs.length == 2, "Invalid number of proofs");

        // Extract account proof
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            ScrvusdVerifierCore.SCRVUSD_HASH,
            stateRoot,
            proofs[0].toList()
        );
        require(account.exists, "scrvUSD account does not exist");

        Verifier.SlotValue memory slot = Verifier.extractSlotValueFromProof(
            keccak256(abi.encode(PERIOD_SLOT)),
            account.storageRoot,
            proofs[1].toList()
        );
        require(slot.exists);

        return slot.value;
    }
}