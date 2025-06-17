import json
import os
from getpass import getpass

import boa
import boa_solidity
from eth_account import account
from proof import generate_message_digest_proof
from web3 import Web3

AGENT = 1  # ALTER
CHAIN_ID = 56  # ALTER
NONCE = 0  # ALTER
MESSAGES = [("0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683", bytes("test", "utf-8"))]  # ALTER
ETH_NETWORK = (
    f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_API_KEY']}"
)
NETWORK = "https://bsc-dataseed2.defibit.io"

eth_web3 = Web3(
    provider=Web3.HTTPProvider(
        f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_API_KEY']}",
    ),
)

l2_web3 = Web3(
    provider=Web3.HTTPProvider(
        NETWORK,
    ),
)


def deploy(boracle, relayer):
    verifier = boa_solidity.load_partial_solc(
        "contracts/xdao/contracts/verifiers/MessageDigestVerifier.sol",
        compiler_args={
            "solc_version": "0.8.18",
            "optimize": True,
            "optimize_runs": 200,
            "evm_version": "paris",
            "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=/Users/romanagureev/.brownie/packages/hamdiallam/Solidity-RLP@2.0.7",
        },
    ).deploy(boracle, relayer)
    return verifier


def send_blockhash():
    boa.fork(ETH_NETWORK, block_identifier="latest")
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    # boa.set_network_env(ETH_NETWORK)
    # boa.env.add_account(account_load('curve'))

    block_num = boa.eval("block.number")
    print(f"Latest block number: {block_num}")
    sender = boa.load_partial("contracts/xdao/contracts/messengers/LayerZeroSender.vy").at(
        "0x49cdecc38B4CAf6a07c13558A32820333BC2aB61"
    )
    sender.transmit(block_num - 64 - 3, value=sender.quote())


def simulate(relayer, verifier):
    relayer = boa.load_partial("contracts/xdao/contracts/xgov/XYZRelayer.vy").at(relayer)
    with boa.env.prank(relayer.OWNERSHIP_AGENT()):
        relayer.set_messenger(verifier)
    # boa.env.time_travel(seconds=86400 * 7)

    proofs = generate_message_digest_proof(
        eth_web3, agent=1, chain_id=56, nonce=0, block_number=21458536, log=True
    )
    verifier.verifyMessagesByBlockHash(
        1,
        MESSAGES,
        bytes.fromhex(proofs[0]),
        bytes.fromhex(proofs[1]),
    )
    assert verifier.nonce(1) == 1
    assert verifier.nonce(2) == 0
    assert verifier.nonce(4) == 0


def account_load(fname):
    path = os.path.expanduser(os.path.join("~", ".brownie", "accounts", fname + ".json"))
    with open(path, "r") as f:
        pkey = account.decode_keyfile_json(json.load(f), getpass())
        return account.Account.from_key(pkey)


if __name__ == "__main__":
    # send_blockhash()
    # boa.fork(NETWORK, block_identifier='latest')
    # boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    boa.set_network_env(NETWORK)
    boa.env.add_account(account_load("curve"))
    verifier = deploy(
        "0x7cDe6Ef7e2e2FD3B6355637F1303586D7262ba37",
        "0x37b6d6d425438a9f8e40C8B4c06c10560967b678",
    )
    # simulate(
    #     "0x37b6d6d425438a9f8e40C8B4c06c10560967b678",
    #     verifier,
    # )
