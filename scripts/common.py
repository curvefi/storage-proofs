import json
import os
from getpass import getpass

from eth_account import account

ETH_NETWORK = f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_API_KEY']}"  # ALTER
L2_NETWORKS = {  # ALTER
    "base": "https://mainnet.base.org",
    "taiko": "https://rpc.taiko.xyz",
}

CHAIN_IDS = {
    "base": 8453,
    "taiko": 167000,
}


def account_load_pkey(fname):
    path = os.path.expanduser(os.path.join("~", ".brownie", "accounts", fname + ".json"))
    with open(path, "r") as f:
        pkey = account.decode_keyfile_json(json.load(f), getpass())
        return pkey


wallet = None  # Account.from_key(account_load_pkey("curve"))  # ALTER


def send_transaction(tx, l2_web3, wallet):
    tx = tx.build_transaction(
        {
            "from": wallet.address,
            "nonce": l2_web3.eth.get_transaction_count(wallet.address),
        }
    )
    signed_tx = l2_web3.eth.account.sign_transaction(tx, private_key=wallet.key)
    l2_web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return l2_web3.eth.wait_for_transaction_receipt(signed_tx)
