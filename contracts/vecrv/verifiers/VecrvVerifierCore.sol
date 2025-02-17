// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";


interface IVecrvOracle {
    struct Point {
        int128 bias;
        int128 slope;
        uint256 ts;
        uint256 blk;
    }

    struct LockedBalance {
        int128 amount;
        uint256 end;
    }

    function update_balance(
        address _user,
        uint256 _user_point_epoch,
        Point memory _user_point_history,
        LockedBalance memory _locked
    ) external;

    function update_total(
        uint256 _epoch,
        Point memory _point_history,
        int128[] memory _slope_changes
    ) external;
}

// @dev Base here refers to the fact that this is a base
// contract that is inherited by other contracts and not
// a contract related to the Base L2.
abstract contract VecrvVerifierCore {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    uint256 private constant WEEK = 7 * 86400;
    uint256 public constant MIN_SLOPE_CHANGES_CNT = 4; // 1 month

    address private constant VOTING_ESCROW = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2;
    bytes32 private constant VOTING_ESCROW_HASH = keccak256(abi.encodePacked(VOTING_ESCROW));

    uint256 private constant EPOCH_SLOT = 3;
    uint256 private constant USER_POINT_EPOCH_SLOT = 6;
    uint256 private constant POINT_HISTORY_SLOT = 4;
    uint256 private constant USER_POINT_HISTORY_SLOT = 5;
    uint256 private constant LOCKED_BALANCE_SLOT = 2;
    uint256 private constant SLOPE_CHANGES_SLOT = 7;

    // update balance
    uint256 private constant USER_POINT_EPOCH_PROOF_I = 0;
    uint256 private constant USER_POINT_HISTORY_PROOF_I = USER_POINT_EPOCH_PROOF_I + 1;
    uint256 private constant LOCKED_BALANCE_PROOF_I = USER_POINT_HISTORY_PROOF_I + 4;

    // update total
    uint256 private constant EPOCH_PROOF_I = 0;
    uint256 private constant POINT_HISTORY_PROOF_I = EPOCH_PROOF_I + 1;
    uint256 private constant SLOPE_CHANGES_PROOF_I = POINT_HISTORY_PROOF_I + 4;

    address public immutable VE_ORACLE;

    constructor(address _ve_oracle) {
        VE_ORACLE = _ve_oracle;
    }

    /// @dev Update total parameters with proofs
    function _updateTotal(
        bytes32 storageRoot,
        RLPReader.RLPItem[] memory proofs
    ) internal {
        require(proofs.length >= SLOPE_CHANGES_PROOF_I + MIN_SLOPE_CHANGES_CNT, "Invalid number of total proofs");

        // Extract slot values
        uint256 epoch = Verifier.extractSlotValueFromProof(
            keccak256(abi.encode(EPOCH_SLOT)),
            storageRoot,
            proofs[EPOCH_PROOF_I].toList()
        ).value;
        IVecrvOracle.Point memory point_history = _extract_point(
            POINT_HISTORY_PROOF_I,
            keccak256(abi.encode(uint256(keccak256(abi.encode(POINT_HISTORY_SLOT))) + epoch)),
            storageRoot,
            proofs
        );
        uint256 start = WEEK + point_history.ts / WEEK * WEEK;
        int128[] memory slope_changes = new int128[](proofs.length - SLOPE_CHANGES_PROOF_I);
        for (uint256 i = 0; i < proofs.length - SLOPE_CHANGES_PROOF_I; ++i) {
            slope_changes[i] = int128(int256(Verifier.extractSlotValueFromProof(
                keccak256(abi.encode(keccak256(abi.encode(SLOPE_CHANGES_SLOT, start + i * WEEK)))),
                storageRoot,
                proofs[SLOPE_CHANGES_PROOF_I + i].toList()
            ).value));
        }

        return IVecrvOracle(VE_ORACLE).update_total(
            epoch,
            point_history,
            slope_changes
        );
    }

    /// @dev Update user's balance with proofs
    function _updateBalance(
        address user,
        bytes32 storageRoot,
        RLPReader.RLPItem[] memory proofs
    ) internal {
        require(proofs.length == LOCKED_BALANCE_PROOF_I + 2, "Invalid number of balance proofs");

        // Extract slot values
        uint256 user_point_epoch = Verifier.extractSlotValueFromProof(
            keccak256(
                abi.encode(keccak256(abi.encode(USER_POINT_EPOCH_SLOT, user)))
            ),
            storageRoot,
            proofs[USER_POINT_EPOCH_PROOF_I].toList()
        ).value;
        IVecrvOracle.Point memory user_point_history = _extract_point(
            USER_POINT_HISTORY_PROOF_I,
            keccak256(abi.encode(uint256(keccak256(abi.encode(keccak256(abi.encode(USER_POINT_HISTORY_SLOT, user))))) + user_point_epoch)),
            storageRoot,
            proofs
        );
        IVecrvOracle.LockedBalance memory locked = _extract_locked_balance(
            LOCKED_BALANCE_PROOF_I,
            keccak256(abi.encode(keccak256(abi.encode(LOCKED_BALANCE_SLOT, user)))),
            storageRoot,
            proofs
        );

        return IVecrvOracle(VE_ORACLE).update_balance(
            user,
            user_point_epoch,
            user_point_history,
            locked
        );
    }

    function _extract_point(uint256 proof_i, bytes32 slot, bytes32 storageRoot, RLPReader.RLPItem[] memory proofs) internal returns (IVecrvOracle.Point memory p) {
        p.bias = int128(int256(Verifier.extractSlotValueFromProof(keccak256(abi.encode(slot)), storageRoot, proofs[proof_i].toList()).value));
        p.slope = int128(int256(Verifier.extractSlotValueFromProof(keccak256(abi.encode(uint256(slot) + 1)), storageRoot, proofs[proof_i + 1].toList()).value));
        p.ts = Verifier.extractSlotValueFromProof(keccak256(abi.encode(uint256(slot) + 2)), storageRoot, proofs[proof_i + 2].toList()).value;
        p.blk = Verifier.extractSlotValueFromProof(keccak256(abi.encode(uint256(slot) + 3)), storageRoot, proofs[proof_i + 3].toList()).value;
    }

    function _extract_locked_balance(uint256 proof_i, bytes32 slot, bytes32 storageRoot, RLPReader.RLPItem[] memory proofs) internal returns (IVecrvOracle.LockedBalance memory lb) {
        lb.amount = int128(int256(Verifier.extractSlotValueFromProof(keccak256(abi.encode(slot)), storageRoot, proofs[proof_i].toList()).value));
        lb.end = Verifier.extractSlotValueFromProof(keccak256(abi.encode(uint256(slot) + 1)), storageRoot, proofs[proof_i + 1].toList()).value;
    }

    function _extractAccountStorageRoot(
        bytes32 state_root_hash,
        RLPReader.RLPItem memory account_proof
    ) internal returns (bytes32) {
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            VOTING_ESCROW_HASH,
            state_root_hash,
            account_proof.toList()
        );
        require(account.exists, "VotingEscrow account does not exist");
        return account.storageRoot;
    }
}
