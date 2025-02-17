// SPDX-License-Identifier: MIT
pragma solidity 0.8.18;

import {RLPReader} from "hamdiallam/Solidity-RLP@2.0.7/contracts/RLPReader.sol";
import {StateProofVerifier as Verifier} from "../../xdao/contracts/libs/StateProofVerifier.sol";


interface IVecrvOracle {
    function update_delegation(
        address from,
        address to,
        uint256 block_number
    ) external;
}

// @dev Base here refers to the fact that this is a base
// contract that is inherited by other contracts and not
// a contract related to the Base L2.
abstract contract DelegationVerifierCore {
    using RLPReader for bytes;
    using RLPReader for RLPReader.RLPItem;

    // Common constants
    address private constant VE_DELEGATE = 0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2;
    bytes32 private constant VE_DELEGATE_HASH = keccak256(abi.encodePacked(VE_DELEGATE));

    address public immutable VE_ORACLE;

    constructor(address _ve_oracle) {
        VE_ORACLE = _ve_oracle;
    }

    /// @dev Update delegation using proof. `blockNumber` is used for updates linearization
    function _updateDelegation(
        address from,
        uint256 blockNumber,
        bytes32 stateRoot,
        bytes memory proofRlp
    ) internal {
        RLPReader.RLPItem[] memory proofs = proofRlp.toRlpItem().toList();
        require(proofs.length == 2, "Invalid number of proofs");

        // Extract account proof
        Verifier.Account memory account = Verifier.extractAccountFromProof(
            VE_DELEGATE_HASH,
            stateRoot,
            proofs[0].toList()
        );
        require(account.exists, "Delegate account does not exist");

        // Extract slot values
        address to = address(uint160(Verifier.extractSlotValueFromProof(
            keccak256(abi.encode(
                keccak256(abi.encode(
                    keccak256(abi.encode(1, block.chainid)), // slot of delegation_from[chain.id][]
                    from
                ))
            )),
            account.storageRoot,
            proofs[1].toList()
        ).value));
        require(to != VE_DELEGATE, "Delegate not set");

        return IVecrvOracle(VE_ORACLE).update_delegation(from, to, blockNumber);
    }
}
