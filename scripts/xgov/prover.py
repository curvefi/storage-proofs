import sys

from proof import generate_message_digest_proof
from scripts.common import CHAIN_IDS, ETH_NETWORK, L2_NETWORKS, send_transaction, wallet
from web3 import Web3
from web3.contract import Contract

from scripts.blockhash.blockhash import fetch_block_number

CHAIN = "bsc"  # ALTER
BLOCK_NUMBER = None  # ALTER, None will take latest available
L2_NETWORK = L2_NETWORKS[CHAIN]
CHAIN_ID = CHAIN_IDS[CHAIN]

VERIFIER = {
    "bsc": "0x74d6aABD6197E83d963F0B48be9C034F93E8E66d",
    "sonic": "0x3d8EADb739D1Ef95dd53D718e4810721837c69c1",
}[CHAIN]
VERSION = {
    "bsc": "blockhash",
    "sonic": "stateroot",
}[CHAIN]

AGENT = 1  # ALTER
NONCE = 0  # ALTER
MESSAGES = [
    ("0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683", bytes("test", "utf-8"))
]  # ALTER

eth_web3 = Web3(provider=Web3.HTTPProvider(ETH_NETWORK))
l2_web3 = Web3(provider=Web3.HTTPProvider(L2_NETWORK))


class XGov:
    def __init__(self, verifier=None):
        # fmt: off
        self.broadcaster = eth_web3.eth.contract(address="0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2", abi=[{"name":"Broadcast","inputs":[{"name":"agent","type":"uint256","indexed":true},{"name":"chain_id","type":"uint256","indexed":true},{"name":"nonce","type":"uint256","indexed":false},{"name":"digest","type":"bytes32","indexed":false},{"name":"deadline","type":"uint256","indexed":false}],"anonymous":false,"type":"event"},{"name":"ApplyAdmins","inputs":[{"name":"admins","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}],"indexed":false}],"anonymous":false,"type":"event"},{"name":"CommitAdmins","inputs":[{"name":"future_admins","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}],"indexed":false}],"anonymous":false,"type":"event"},{"stateMutability":"nonpayable","type":"constructor","inputs":[{"name":"_admins","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}]}],"outputs":[]},{"stateMutability":"nonpayable","type":"function","name":"broadcast","inputs":[{"name":"_chain_id","type":"uint256"},{"name":"_messages","type":"tuple[]","components":[{"name":"target","type":"address"},{"name":"data","type":"bytes"}]}],"outputs":[]},{"stateMutability":"nonpayable","type":"function","name":"broadcast","inputs":[{"name":"_chain_id","type":"uint256"},{"name":"_messages","type":"tuple[]","components":[{"name":"target","type":"address"},{"name":"data","type":"bytes"}]},{"name":"_ttl","type":"uint256"}],"outputs":[]},{"stateMutability":"nonpayable","type":"function","name":"commit_admins","inputs":[{"name":"_future_admins","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}]}],"outputs":[]},{"stateMutability":"nonpayable","type":"function","name":"apply_admins","inputs":[],"outputs":[]},{"stateMutability":"view","type":"function","name":"version","inputs":[],"outputs":[{"name":"","type":"string"}]},{"stateMutability":"view","type":"function","name":"admins","inputs":[],"outputs":[{"name":"","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}]}]},{"stateMutability":"view","type":"function","name":"future_admins","inputs":[],"outputs":[{"name":"","type":"tuple","components":[{"name":"ownership","type":"address"},{"name":"parameter","type":"address"},{"name":"emergency","type":"address"}]}]},{"stateMutability":"view","type":"function","name":"nonce","inputs":[{"name":"arg0","type":"uint256"},{"name":"arg1","type":"uint256"}],"outputs":[{"name":"","type":"uint256"}]},{"stateMutability":"view","type":"function","name":"digest","inputs":[{"name":"arg0","type":"uint256"},{"name":"arg1","type":"uint256"},{"name":"arg2","type":"uint256"}],"outputs":[{"name":"","type":"bytes32"}]},{"stateMutability":"view","type":"function","name":"deadline","inputs":[{"name":"arg0","type":"uint256"},{"name":"arg1","type":"uint256"},{"name":"arg2","type":"uint256"}],"outputs":[{"name":"","type":"uint256"}]}])  # noqa
        self.verifier = verifier or l2_web3.eth.contract(address=VERIFIER, abi=[{'inputs': [{'internalType': 'address', 'name': '_block_hash_oracle', 'type': 'address'}, {'internalType': 'address', 'name': '_relayer', 'type': 'address'}], 'stateMutability': 'nonpayable', 'type': 'constructor'}, {'inputs': [], 'name': 'BLOCK_HASH_ORACLE', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [], 'name': 'RELAYER', 'outputs': [{'internalType': 'address', 'name': '', 'type': 'address'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'name': 'nonce', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '_agent', 'type': 'uint256'}, {'components': [{'internalType': 'address', 'name': 'target', 'type': 'address'}, {'internalType': 'bytes', 'name': 'data', 'type': 'bytes'}], 'internalType': 'struct IRelayer.Message[]', 'name': '_messages', 'type': 'tuple[]'}, {'internalType': 'bytes', 'name': '_block_header_rlp', 'type': 'bytes'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyMessagesByBlockHash', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}, {'inputs': [{'internalType': 'uint256', 'name': '_agent', 'type': 'uint256'}, {'components': [{'internalType': 'address', 'name': 'target', 'type': 'address'}, {'internalType': 'bytes', 'name': 'data', 'type': 'bytes'}], 'internalType': 'struct IRelayer.Message[]', 'name': '_messages', 'type': 'tuple[]'}, {'internalType': 'uint256', 'name': '_block_number', 'type': 'uint256'}, {'internalType': 'bytes', 'name': '_proof_rlp', 'type': 'bytes'}], 'name': 'verifyMessagesByStateRoot', 'outputs': [], 'stateMutability': 'nonpayable', 'type': 'function'}])  # noqa
        # fmt: on

    def verify_messages(self, agent=AGENT, messages=MESSAGES, block_number=None):
        if (nonce := self._verify_messages_needed(agent)) is None:
            return

        if not block_number:
            block_number = fetch_block_number(CHAIN, l2_web3, block_number=block_number)

        proofs = generate_message_digest_proof(
            eth_web3,
            agent=agent,
            chain_id=CHAIN_ID,
            nonce=nonce,
            block_number=block_number,
        )

        match VERSION:
            case "blockhash":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyMessagesByBlockHash(
                        agent,
                        messages,
                        bytes.fromhex(proofs[0]),
                        bytes.fromhex(proofs[1]),
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyMessagesByBlockHash(
                        agent,
                        messages,
                        bytes.fromhex(proofs[0]),
                        bytes.fromhex(proofs[1]),
                    )
            case "stateroot":
                if isinstance(self.verifier, Contract):
                    tx = self.verifier.functions.verifyMessagesByStateRoot(
                        agent, messages, block_number, bytes.fromhex(proofs[1])
                    )
                    send_transaction(tx, l2_web3, wallet)
                else:
                    self.verifier.verifyMessagesByStateRoot(
                        agent, messages, block_number, bytes.fromhex(proofs[1])
                    )
        print(f"Submitted proof")

    def _verify_messages_needed(self, agent):
        eth_nonce = self.broadcaster.functions.nonce(agent).call()
        l2_nonce = self.verifier.functions.nonce(agent).call()
        return l2_nonce if eth_nonce > l2_nonce else None


def get_agent():
    try:
        agent = int(sys.argv[-1])
        assert agent in [1, 2, 4]
    except:
        agent = AGENT
    return agent


if __name__ == "__main__":
    XGov().verify_messages()
