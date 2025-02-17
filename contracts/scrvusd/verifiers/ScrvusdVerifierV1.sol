// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";

uint256 constant PARAM_CNT = 2 + 5;
uint256 constant PROOF_CNT = 1 + PARAM_CNT;

interface IScrvusdOracle {
    function update_price(
        uint256[PARAM_CNT] memory _parameters,
        uint256 _ts,
        uint256 _block_number
    ) external returns (uint256);
}

interface IBlockHashOracle {
    function get_block_hash(uint256 _number) external view returns (bytes32);
    function get_state_root(uint256 _number) external view returns (bytes32);
}

contract ScrvusdVerifierV1 {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    // Common constants
    address constant SCRVUSD = 0x0655977FEb2f289A4aB78af67BAB0d17aAb84367;
    bytes32 constant SCRVUSD_HASH = keccak256(abi.encodePacked(SCRVUSD));

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
    address public immutable BLOCK_HASH_ORACLE;

    constructor(address _block_hash_oracle, address _scrvusd_oracle)
    {
        BLOCK_HASH_ORACLE = _block_hash_oracle;
        SCRVUSD_ORACLE = _scrvusd_oracle;
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
        uint256 ts,
        uint256 number
    ) internal returns (uint256) {
        return IScrvusdOracle(SCRVUSD_ORACLE).update_price(params, ts, number);
    }
}