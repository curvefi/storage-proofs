import boa

from web3 import Web3
import json
import os

from getpass import getpass
from eth_account import account


NETWORK = (
    f"https://rpc.soniclabs.com"
)

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


# ---------------------------------- Deploy ---------------------------------- #


def deploy_optimism():
    boracle = boa.load_partial("contracts/blockhash/OptimismBlockHashOracle.vy").deploy()
    apply_block_hash(boracle)
    return boracle


def deploy_sonic():
    boracle = boa.load_partial("contracts/blockhash/SonicBlockHashOracle.vy").deploy(
        "0x836664B0c0CB29B7877bCcF94159CC996528F2C3"
    )
    apply_state_root(boracle)
    return boracle


def deploy_taiko():
    boracle = boa.load_partial("contracts/blockhash/TaikoBlockHashOracle.vy").deploy()
    find_state_root(boracle)
    return boracle


# -------------------------------- Simulations ------------------------------- #


def apply_block_hash(boracle):
    number = boracle.apply()
    blockhash = boracle.get_block_hash(number)
    print(f"Applied block: {number}, {blockhash.hex()}")
    assert blockhash == eth_web3.eth.get_block(number)["hash"]


def apply_state_root(boracle):
    number = boracle.apply()
    stateroot = boracle.get_state_root(number)
    print(f"Applied block: {number}, {stateroot.hex()}")
    assert stateroot == eth_web3.eth.get_block(number)["stateRoot"]


def find_block_hash(boracle):
    number = boracle.find_known_block_number(
        eth_web3.eth.get_block("latest")
    )
    blockhash = boracle.get_block_hash(number)
    print(f"Found block: {number}, {blockhash.hex()}")
    assert blockhash == eth_web3.eth.get_block(number)["hash"]


def find_state_root(boracle):
    number = boracle.find_known_block_number(
        eth_web3.eth.get_block("latest")
    )
    stateroot = boracle.get_state_root(number)
    print(f"Found block: {number}, {stateroot.hex()}")
    assert stateroot == eth_web3.eth.get_block(number)["stateRoot"]


# ------------------------------------ Run ----------------------------------- #


def account_load(fname):
    path = os.path.expanduser(os.path.join("~", ".brownie", "accounts", fname + ".json"))
    with open(path, "r") as f:
        pkey = account.decode_keyfile_json(json.load(f), getpass())
        return account.Account.from_key(pkey)


if __name__ == "__main__":
    boa.fork(NETWORK, block_identifier="latest")
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    # boa.set_network_env(NETWORK)
    # boa.env.add_account(account_load('curve'))
    contract = deploy_sonic()
