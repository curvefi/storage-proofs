import boa
import boa_solidity

from web3 import Web3
import json
import os

from getpass import getpass
from eth_account import account

from proof import generate_proof, submit_proof


NETWORK = (
    f"https://opt-mainnet.g.alchemy.com/v2/{os.environ['WEB3_OPTIMISM_MAINNET_ALCHEMY_API_KEY']}"
)

SCRVUSD = "0x0655977FEb2f289A4aB78af67BAB0d17aAb84367"

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


def deploy():
    boracle = boa.load_partial("contracts/blockhash/OptimismBlockHashOracle.vy").deploy()
    soracle = boa.load_partial("contracts/scrvusd/oracles/ScrvusdOracleV1.vy").deploy(
        10**18, 10**13
    )

    verifier = boa_solidity.load_partial_solc(
        "contracts/scrvusd/verifiers/ScrvusdVerifier.sol",
        compiler_args={
            "solc_version": "0.8.18",
            "optimize": True,
            "optimize_runs": 200,
            "evm_version": "paris",
            "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=/Users/romanagureev/.brownie/packages/hamdiallam/Solidity-RLP@2.0.7",
        },
    ).deploy(boracle.address, soracle.address)

    soracle.set_verifier(verifier)

    return boracle, soracle, verifier


def prove(boracle, soracle, verifier):
    number = boracle.apply()
    print(f"Applied block: {number}, {boracle.get_block_hash(number).hex()}")

    proofs = generate_proof(eth_web3, number, log=True)
    submit_proof(proofs, verifier)
    print("Sibmitted proof")


def simulate(boracle, soracle, verifier):
    print(f"Initial price: {soracle.price_v1()}")
    prove(boracle, soracle, verifier)
    print(f"Price just after: {soracle.price_v1()}")
    already = 0
    for i in [1, 2, 5, 10, 60, 3600, 10 * 3600, 86400, 7 * 86400]:
        boa.env.time_travel(seconds=i - already)
        already = i
        print(f"Price after {i: 8} sec: {soracle.price_v1()}")


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
    boracle, soracle, prover = deploy()
    simulate(boracle, soracle, prover)
