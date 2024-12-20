import sys

from proof import (
    generate_balance_proof,
    generate_delegation_proof,
    generate_total_proof,
)
from web3 import Web3
from web3.contract import Contract

from scripts.blockhash.blockhash import fetch_block_number
from scripts.common import CHAIN_IDS, ETH_NETWORK, L2_NETWORKS, send_transaction, wallet

CHAIN = "base"  # ALTER
BLOCK_NUMBER = None  # ALTER, None will take latest available
L2_NETWORK = L2_NETWORKS[CHAIN]
CHAIN_ID = CHAIN_IDS[CHAIN]

B_ORACLE, V_ORACLE, VERIFIER, D_VERIFIER = {
    "base": (
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
    ),  # noqa
}[CHAIN]
VERSION = {
    "base": "blockhash",
    "taiko": "stateroot",
}[CHAIN]

USER = None  # address of the user
REL_BALANCE_THRESHOLD = 1.01  # ALTER: should be >1, 1%
REL_TOTAL_THRESHOLD = 1.01  # ALTER: should be >1, 1%

eth_web3 = Web3(provider=Web3.HTTPProvider(ETH_NETWORK))
l2_web3 = Web3(provider=Web3.HTTPProvider(L2_NETWORK))


class Vecrv:
    def __init__(self, verifier=None):
        # fmt: off
        self.vecrv = eth_web3.eth.contract(address="0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2", abi=[{'name': 'CommitOwnership', 'inputs': [{'type': 'address', 'name': 'admin', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'ApplyOwnership', 'inputs': [{'type': 'address', 'name': 'admin', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'Deposit', 'inputs': [{'type': 'address', 'name': 'provider', 'indexed': True}, {'type': 'uint256', 'name': 'value', 'indexed': False}, {'type': 'uint256', 'name': 'locktime', 'indexed': True}, {'type': 'int128', 'name': 'type', 'indexed': False}, {'type': 'uint256', 'name': 'ts', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'Withdraw', 'inputs': [{'type': 'address', 'name': 'provider', 'indexed': True}, {'type': 'uint256', 'name': 'value', 'indexed': False}, {'type': 'uint256', 'name': 'ts', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'Supply', 'inputs': [{'type': 'uint256', 'name': 'prevSupply', 'indexed': False}, {'type': 'uint256', 'name': 'supply', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'outputs': [], 'inputs': [{'type': 'address', 'name': 'token_addr'}, {'type': 'string', 'name': '_name'}, {'type': 'string', 'name': '_symbol'}, {'type': 'string', 'name': '_version'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'name': 'commit_transfer_ownership', 'outputs': [], 'inputs': [{'type': 'address', 'name': 'addr'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 37597}, {'name': 'apply_transfer_ownership', 'outputs': [], 'inputs': [], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 38497}, {'name': 'commit_smart_wallet_checker', 'outputs': [], 'inputs': [{'type': 'address', 'name': 'addr'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 36307}, {'name': 'apply_smart_wallet_checker', 'outputs': [], 'inputs': [], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 37095}, {'name': 'get_last_user_slope', 'outputs': [{'type': 'int128', 'name': ''}], 'inputs': [{'type': 'address', 'name': 'addr'}], 'stateMutability': 'view', 'type': 'function', 'gas': 2569}, {'name': 'user_point_history__ts', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': '_addr'}, {'type': 'uint256', 'name': '_idx'}], 'stateMutability': 'view', 'type': 'function', 'gas': 1672}, {'name': 'locked__end', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': '_addr'}], 'stateMutability': 'view', 'type': 'function', 'gas': 1593}, {'name': 'checkpoint', 'outputs': [], 'inputs': [], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 37052342}, {'name': 'deposit_for', 'outputs': [], 'inputs': [{'type': 'address', 'name': '_addr'}, {'type': 'uint256', 'name': '_value'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 74279891}, {'name': 'create_lock', 'outputs': [], 'inputs': [{'type': 'uint256', 'name': '_value'}, {'type': 'uint256', 'name': '_unlock_time'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 74281465}, {'name': 'increase_amount', 'outputs': [], 'inputs': [{'type': 'uint256', 'name': '_value'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 74280830}, {'name': 'increase_unlock_time', 'outputs': [], 'inputs': [{'type': 'uint256', 'name': '_unlock_time'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 74281578}, {'name': 'withdraw', 'outputs': [], 'inputs': [], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 37223566}, {'name': 'balanceOf', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': 'addr'}], 'stateMutability': 'view', 'type': 'function'}, {'name': 'balanceOf', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': 'addr'}, {'type': 'uint256', 'name': '_t'}], 'stateMutability': 'view', 'type': 'function'}, {'name': 'balanceOfAt', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': 'addr'}, {'type': 'uint256', 'name': '_block'}], 'stateMutability': 'view', 'type': 'function', 'gas': 514333}, {'name': 'totalSupply', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function'}, {'name': 'totalSupply', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'uint256', 'name': 't'}], 'stateMutability': 'view', 'type': 'function'}, {'name': 'totalSupplyAt', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'uint256', 'name': '_block'}], 'stateMutability': 'view', 'type': 'function', 'gas': 812560}, {'name': 'changeController', 'outputs': [], 'inputs': [{'type': 'address', 'name': '_newController'}], 'stateMutability': 'nonpayable', 'type': 'function', 'gas': 36907}, {'name': 'token', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 1841}, {'name': 'supply', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 1871}, {'name': 'locked', 'outputs': [{'type': 'int128', 'name': 'amount'}, {'type': 'uint256', 'name': 'end'}], 'inputs': [{'type': 'address', 'name': 'arg0'}], 'stateMutability': 'view', 'type': 'function', 'gas': 3359}, {'name': 'epoch', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 1931}, {'name': 'point_history', 'outputs': [{'type': 'int128', 'name': 'bias'}, {'type': 'int128', 'name': 'slope'}, {'type': 'uint256', 'name': 'ts'}, {'type': 'uint256', 'name': 'blk'}], 'inputs': [{'type': 'uint256', 'name': 'arg0'}], 'stateMutability': 'view', 'type': 'function', 'gas': 5550}, {'name': 'user_point_history', 'outputs': [{'type': 'int128', 'name': 'bias'}, {'type': 'int128', 'name': 'slope'}, {'type': 'uint256', 'name': 'ts'}, {'type': 'uint256', 'name': 'blk'}], 'inputs': [{'type': 'address', 'name': 'arg0'}, {'type': 'uint256', 'name': 'arg1'}], 'stateMutability': 'view', 'type': 'function', 'gas': 6079}, {'name': 'user_point_epoch', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [{'type': 'address', 'name': 'arg0'}], 'stateMutability': 'view', 'type': 'function', 'gas': 2175}, {'name': 'slope_changes', 'outputs': [{'type': 'int128', 'name': ''}], 'inputs': [{'type': 'uint256', 'name': 'arg0'}], 'stateMutability': 'view', 'type': 'function', 'gas': 2166}, {'name': 'controller', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2081}, {'name': 'transfersEnabled', 'outputs': [{'type': 'bool', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2111}, {'name': 'name', 'outputs': [{'type': 'string', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 8543}, {'name': 'symbol', 'outputs': [{'type': 'string', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 7596}, {'name': 'version', 'outputs': [{'type': 'string', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 7626}, {'name': 'decimals', 'outputs': [{'type': 'uint256', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2231}, {'name': 'future_smart_wallet_checker', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2261}, {'name': 'smart_wallet_checker', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2291}, {'name': 'admin', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2321}, {'name': 'future_admin', 'outputs': [{'type': 'address', 'name': ''}], 'inputs': [], 'stateMutability': 'view', 'type': 'function', 'gas': 2351}])  # noqa

        self.verifier = verifier or l2_web3.eth.contract(address=VERIFIER, abi=[{'inputs': [{'internalType': 'address', 'name': '_block_hash_oracle', 'type': 'address'}, {'internalType': 'address', 'name': '_vecrv_oracle', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'inputs': [], 'name': 'BLOCK_HASH_ORACLE', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'MIN_SLOPE_CHANGES_CNT', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'VE_ORACLE', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_user', 'type': 'address'}, {'internalType': 'bytes', 'name': '_block_header_rlp', 'type': 'bytes'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyBalanceByBlockHash', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_user', 'type': 'address'}, {'internalType': 'uint256', 'name': '_block_number', 'type': 'uint256'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyBalanceByStateRoot', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'bytes', 'name': '_block_header_rlp', 'type': 'bytes'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyTotalByBlockHash', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '_block_number', 'type': 'uint256'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyTotalByStateRoot', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}])  # noqa
        self.voracle = l2_web3.eth.contract(address=V_ORACLE, abi=[{'name': 'UpdateTotal', 'inputs': [{'name': '_epoch', 'type': 'uint256', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'UpdateBalance', 'inputs': [{'name': '_user', 'type': 'address', 'indexed': False}, {'name': '_user_point_epoch', 'type': 'uint256', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'Delegate', 'inputs': [{'name': '_from', 'type': 'address', 'indexed': False}, {'name': '_to', 'type': 'address', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleGranted', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'account', 'type': 'address', 'indexed': True}, {'name': 'sender', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleAdminChanged', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'previousAdminRole', 'type': 'bytes32', 'indexed': True}, {'name': 'newAdminRole', 'type': 'bytes32', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleRevoked', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'account', 'type': 'address', 'indexed': True}, {'name': 'sender', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'stateMutability': 'view', 'type': 'function', 'name': 'supportsInterface', 'inputs': [{'name': 'interface_id', 'type': 'bytes4'}], 'outputs': [{'name': '', 'type': 'bool'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'hasRole', 'inputs': [{'name': 'arg0', 'type': 'bytes32'}, {'name': 'arg1', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'bool'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'DEFAULT_ADMIN_ROLE', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'grantRole', 'inputs': [{'name': 'role', 'type': 'bytes32'}, {'name': 'account', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'revokeRole', 'inputs': [{'name': 'role', 'type': 'bytes32'}, {'name': 'account', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_target', 'inputs': [{'name': '_from', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_source', 'inputs': [{'name': '_to', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'balanceOf', 'inputs': [{'name': '_user', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'balanceOf', 'inputs': [{'name': '_user', 'type': 'address'}, {'name': '_timestamp', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'totalSupply', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'totalSupply', 'inputs': [{'name': '_timestamp', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'get_last_user_slope', 'inputs': [{'name': 'addr', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'int128'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'locked__end', 'inputs': [{'name': '_addr', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_balance', 'inputs': [{'name': '_user', 'type': 'address'}, {'name': '_user_point_epoch', 'type': 'uint256'}, {'name': '_user_point_history', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}, {'name': '_locked', 'type': 'tuple', 'components': [{'name': 'amount', 'type': 'int128'}, {'name': 'end', 'type': 'uint256'}]}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_total', 'inputs': [{'name': '_epoch', 'type': 'uint256'}, {'name': '_point_history', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}, {'name': '_slope_changes', 'type': 'int128[]'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_delegation', 'inputs': [{'name': '_from', 'type': 'address'}, {'name': '_to', 'type': 'address'}, {'name': '_block_number', 'type': 'uint256'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'BALANCE_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'TOTAL_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'DELEGATION_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'epoch', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'point_history', 'inputs': [{'name': 'arg0', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'user_point_epoch', 'inputs': [{'name': 'arg0', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'user_point_history', 'inputs': [{'name': 'arg0', 'type': 'address'}, {'name': 'arg1', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'locked', 'inputs': [{'name': 'arg0', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'amount', 'type': 'int128'}, {'name': 'end', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'slope_changes', 'inputs': [{'name': 'arg0', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'int128'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'name', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'symbol', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'decimals', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'version', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'nonpayable', 'type': 'constructor', 'inputs': [], 'outputs': []}])  # noqa
        # fmt: on

    def verify_balance(self, user, block_number=None):
        assert user, "Specify user"
        if not self._verify_balance_needed(user):
            return

        if not block_number:
            block_number = fetch_block_number(CHAIN, l2_web3, block_number=block_number)

        proofs = generate_balance_proof(user, eth_web3, block_number)

        match VERSION:
            case "blockhash":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyBalanceByBlockHash(
                        user, bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyBalanceByBlockHash(
                        user, bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
            case "stateroot":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyBalanceByStateRoot(
                        user, block_number, bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyBalanceByStateRoot(
                        user, block_number, bytes.fromhex(proofs[1])
                    )
        print(f"Submitted proof")

    def _verify_balance_needed(self, user):
        eth_balance = self.vecrv.functions.balanceOf(user).call()
        l2_balance = self.voracle.functions.balanceOf(user).call()
        return (
            abs(l2_balance - eth_balance) / max(eth_balance, 1) >= REL_BALANCE_THRESHOLD
        )

    def verify_total(self, block_number=None, **kwargs):
        if not self._verify_total_needed():
            return

        if not block_number:
            block_number = fetch_block_number(CHAIN, l2_web3, block_number=block_number)

        proofs = generate_total_proof(eth_web3, block_number=block_number, **kwargs)

        match VERSION:
            case "blockhash":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyTotalByBlockHash(
                        bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyTotalByBlockHash(
                        bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
            case "stateroot":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyTotalByStateRoot(
                        block_number, bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyTotalByStateRoot(
                        block_number, bytes.fromhex(proofs[1])
                    )
        print(f"Submitted proof")

    def _verify_total_needed(self):
        eth_total_supply = self.vecrv.functions.totalSupply().call()
        l2_total_supply = self.voracle.functions.totalSupply().call()
        return (
            abs(l2_total_supply - eth_total_supply) / max(eth_total_supply, 1)
            >= REL_BALANCE_THRESHOLD
        )


class Delegate:
    def __init__(self, d_verifier=None):
        # fmt: off
        self.delegate = eth_web3.eth.contract(address="", abi=[{'name': 'AllowDelegation', 'inputs': [{'name': '_chain_id', 'type': 'uint256', 'indexed': True}, {'name': '_to', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'name': 'Delegate', 'inputs': [{'name': '_chain_id', 'type': 'uint256', 'indexed': True}, {'name': '_from', 'type': 'address', 'indexed': True}, {'name': '_to', 'type': 'address', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'OwnershipTransferred', 'inputs': [{'name': 'previous_owner', 'type': 'address', 'indexed': True}, {'name': 'new_owner', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'transfer_ownership', 'inputs': [{'name': 'new_owner', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'owner', 'inputs': [], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_target', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_from', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_source', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_to', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_allowed', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_to', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'bool'}]}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'delegate', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_to', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'allow_delegation', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'allow_delegation', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_allow', 'type': 'bool'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'delegate_from', 'inputs': [{'name': '_chain_id', 'type': 'uint256'}, {'name': '_from', 'type': 'address'}, {'name': '_to', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'version', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'nonpayable', 'type': 'constructor', 'inputs': [], 'outputs': []}])  # noqa

        self.d_verifier = d_verifier or l2_web3.eth.contract(address=D_VERIFIER, abi=[{'inputs': [{'internalType': 'address', 'name': '_block_hash_oracle', 'type': 'address'}, {'internalType': 'address', 'name': '_vecrv_oracle', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'inputs': [], 'name': 'BLOCK_HASH_ORACLE', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'VE_ORACLE', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_from', 'type': 'address'}, {'internalType': 'bytes', 'name': '_block_header_rlp', 'type': 'bytes'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyDelegationByBlockHash', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'address', 'name': '_from', 'type': 'address'}, {'internalType': 'uint256', 'name': '_block_number', 'type': 'uint256'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyDelegationByStateRoot', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}])  # noqa
        self.voracle = l2_web3.eth.contract(address=V_ORACLE, abi=[{'name': 'UpdateTotal', 'inputs': [{'name': '_epoch', 'type': 'uint256', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'UpdateBalance', 'inputs': [{'name': '_user', 'type': 'address', 'indexed': False}, {'name': '_user_point_epoch', 'type': 'uint256', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'Delegate', 'inputs': [{'name': '_from', 'type': 'address', 'indexed': False}, {'name': '_to', 'type': 'address', 'indexed': False}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleGranted', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'account', 'type': 'address', 'indexed': True}, {'name': 'sender', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleAdminChanged', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'previousAdminRole', 'type': 'bytes32', 'indexed': True}, {'name': 'newAdminRole', 'type': 'bytes32', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'name': 'RoleRevoked', 'inputs': [{'name': 'role', 'type': 'bytes32', 'indexed': True}, {'name': 'account', 'type': 'address', 'indexed': True}, {'name': 'sender', 'type': 'address', 'indexed': True}], 'anonymous': False, 'type': 'event'}, {'stateMutability': 'view', 'type': 'function', 'name': 'supportsInterface', 'inputs': [{'name': 'interface_id', 'type': 'bytes4'}], 'outputs': [{'name': '', 'type': 'bool'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'hasRole', 'inputs': [{'name': 'arg0', 'type': 'bytes32'}, {'name': 'arg1', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'bool'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'DEFAULT_ADMIN_ROLE', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'grantRole', 'inputs': [{'name': 'role', 'type': 'bytes32'}, {'name': 'account', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'revokeRole', 'inputs': [{'name': 'role', 'type': 'bytes32'}, {'name': 'account', 'type': 'address'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_target', 'inputs': [{'name': '_from', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'delegation_source', 'inputs': [{'name': '_to', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'address'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'balanceOf', 'inputs': [{'name': '_user', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'balanceOf', 'inputs': [{'name': '_user', 'type': 'address'}, {'name': '_timestamp', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'totalSupply', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'totalSupply', 'inputs': [{'name': '_timestamp', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'get_last_user_slope', 'inputs': [{'name': 'addr', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'int128'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'locked__end', 'inputs': [{'name': '_addr', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_balance', 'inputs': [{'name': '_user', 'type': 'address'}, {'name': '_user_point_epoch', 'type': 'uint256'}, {'name': '_user_point_history', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}, {'name': '_locked', 'type': 'tuple', 'components': [{'name': 'amount', 'type': 'int128'}, {'name': 'end', 'type': 'uint256'}]}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_total', 'inputs': [{'name': '_epoch', 'type': 'uint256'}, {'name': '_point_history', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}, {'name': '_slope_changes', 'type': 'int128[]'}], 'outputs': []}, {'stateMutability': 'nonpayable', 'type': 'function', 'name': 'update_delegation', 'inputs': [{'name': '_from', 'type': 'address'}, {'name': '_to', 'type': 'address'}, {'name': '_block_number', 'type': 'uint256'}], 'outputs': []}, {'stateMutability': 'view', 'type': 'function', 'name': 'BALANCE_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'TOTAL_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'DELEGATION_VERIFIER', 'inputs': [], 'outputs': [{'name': '', 'type': 'bytes32'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'epoch', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'point_history', 'inputs': [{'name': 'arg0', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'user_point_epoch', 'inputs': [{'name': 'arg0', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'user_point_history', 'inputs': [{'name': 'arg0', 'type': 'address'}, {'name': 'arg1', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'bias', 'type': 'int128'}, {'name': 'slope', 'type': 'int128'}, {'name': 'ts', 'type': 'uint256'}, {'name': 'blk', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'locked', 'inputs': [{'name': 'arg0', 'type': 'address'}], 'outputs': [{'name': '', 'type': 'tuple', 'components': [{'name': 'amount', 'type': 'int128'}, {'name': 'end', 'type': 'uint256'}]}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'slope_changes', 'inputs': [{'name': 'arg0', 'type': 'uint256'}], 'outputs': [{'name': '', 'type': 'int128'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'name', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'symbol', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'decimals', 'inputs': [], 'outputs': [{'name': '', 'type': 'uint256'}]}, {'stateMutability': 'view', 'type': 'function', 'name': 'version', 'inputs': [], 'outputs': [{'name': '', 'type': 'string'}]}, {'stateMutability': 'nonpayable', 'type': 'constructor', 'inputs': [], 'outputs': []}])  # noqa
        # fmt: on

    def verify_delegation(self, chain_id, user, block_number=None):
        assert chain_id, "Specify CHAIN_ID"
        assert user, "Specify user"
        if not self._verify_delegation_needed(chain_id, user):
            return

        if not block_number:
            block_number = fetch_block_number(CHAIN, l2_web3, block_number=block_number)

        proofs = generate_delegation_proof(chain_id, user, eth_web3, block_number)

        match VERSION:
            case "blockhash":
                if isinstance(self.d_verifier, Contract):
                    tx = self.d_verifier.functions.verifyDelegationByBlockHash(
                        user, bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.d_verifier.verifyDelegationByBlockHash(
                        user, bytes.fromhex(proofs[0]), bytes.fromhex(proofs[1])
                    )
            case "stateroot":
                if isinstance(self.d_verifier, Contract):
                    tx = self.d_verifier.functions.verifyDelegationByStateRoot(
                        user, block_number, bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.d_verifier.verifyDelegationByStateRoot(
                        user, block_number, bytes.fromhex(proofs[1])
                    )
        print(f"Submitted proof")

    def _verify_delegation_needed(self, chain_id, user):
        eth_target = self.delegate.functions.delegation_target(chain_id, user).call()
        l2_target = self.voracle.functions.delegation_target(user).call()
        return eth_target != l2_target


def get_user():
    try:
        user = str(sys.argv[-1])
        if user.startswith("0x"):
            user = user[2:]
        assert len(user) == 40
        int(user, 16)  # Check that it is hex
        user = "0x" + user
    except:
        user = USER
    return user


if __name__ == "__main__":
    if "balance" in sys.argv:
        Vecrv().verify_balance(user=get_user())
    elif "total" in sys.argv:
        Vecrv().verify_total()
    elif "delegation" in sys.argv:
        Delegate().verify_delegation(chain_id=CHAIN_ID, user=get_user())
