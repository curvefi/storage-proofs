import json
import os
from getpass import getpass

import boa
import boa_solidity
from eth_account import account
from hexbytes import HexBytes
from proof import (
    generate_balance_proof,
    generate_delegation_proof,
    generate_total_proof,
)
from web3 import Web3

NETWORK = f"https://rpc.frax.com"

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
    boracle = boa.load_partial("contracts/blockhash/OptimismBlockHashOracle.vy").at(
        "0xbD2775B8eADaE81501898eB208715f0040E51882"
    )
    voracle = boa.load_partial("contracts/vecrv/oracles/VecrvOracle.vy").deploy()

    verifier = boa_solidity.load_partial_solc(
        "contracts/vecrv/verifiers/VecrvVerifier.sol",
        compiler_args={
            "solc_version": "0.8.18",
            "optimize": True,
            "optimize_runs": 200,
            "evm_version": "paris",
            "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=/Users/romanagureev/.brownie/packages/hamdiallam/Solidity-RLP@2.0.7",
        },
    ).deploy(boracle.address, voracle.address)

    d_verifier = boa_solidity.load_partial_solc(
        "contracts/vecrv/verifiers/DelegationVerifier.sol",
        compiler_args={
            "solc_version": "0.8.18",
            "optimize": True,
            "optimize_runs": 200,
            "evm_version": "paris",
            "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=/Users/romanagureev/.brownie/packages/hamdiallam/Solidity-RLP@2.0.7",
        },
    ).deploy(boracle.address, voracle.address)

    voracle.grantRole(voracle.BALANCE_VERIFIER(), verifier)
    voracle.grantRole(voracle.TOTAL_VERIFIER(), verifier)
    voracle.grantRole(voracle.DELEGATION_VERIFIER(), d_verifier)

    ownership_dao = "0x2c163fe0f079d138b9c04f780d735289344C8B80"
    voracle.grantRole(voracle.DEFAULT_ADMIN_ROLE(), ownership_dao)
    voracle.revokeRole(voracle.DEFAULT_ADMIN_ROLE(), boa.env.eoa)

    return boracle, voracle, verifier, d_verifier


def verify(user, boracle, verifier):
    number = boracle.apply()
    print(f"Applied block: {number}, {boracle.get_block_hash(number).hex()}")

    proofs = generate_balance_proof(user, eth_web3, number, log=True)
    verifier.verifyBalanceByBlockHash(user, HexBytes(proofs[0]), HexBytes(proofs[1]))
    print(f"Sibmitted proof")


def verify_total(boracle, verifier):
    number = boracle.apply()
    print(f"Applied block: {number}, {boracle.get_block_hash(number).hex()}")

    proofs = generate_total_proof(eth_web3, number, log=True)
    verifier.verifyTotalByBlockHash(user, HexBytes(proofs[0]), HexBytes(proofs[1]))
    print(f"Sibmitted proof")


def simulate(user, boracle, voracle, verifier):
    print(
        f"Initial balance: {voracle.balanceOf(user) / 10 ** 18:.2f} / {voracle.totalSupply() / 10 ** 18:.2f}"
    )
    verify(user, boracle, verifier)
    print(
        f"Balance just after: {voracle.balanceOf(user) / 10 ** 18:.2f} / {voracle.totalSupply() / 10 ** 18:.2f}"
    )
    l = voracle.locked(user)
    print(f"Locked balance: {l[0] / 10 ** 18:.2f} until {l[1]}")
    already = 0
    for i in [1, 2, 5, 10, 60, 3600, 10 * 3600, 86400, 7 * 86400]:
        boa.env.time_travel(seconds=i - already)
        already = i
        print(
            f"Balance after {i: 8} sec: {voracle.balanceOf(user) / 10 ** 18:.2f} / {voracle.totalSupply() / 10 ** 18:.2f}"
        )

    print("Verifying total")
    verify(user, boracle, verifier)


def account_load(fname):
    path = os.path.expanduser(
        os.path.join("~", ".brownie", "accounts", fname + ".json")
    )
    with open(path, "r") as f:
        pkey = account.decode_keyfile_json(json.load(f), getpass())
        return account.Account.from_key(pkey)


if __name__ == "__main__":
    # deploy on ETH
    # delegate = boa.load_partial("contracts/vecrv/VecrvDelegate.vy").deploy()

    boa.fork(NETWORK, block_identifier="latest")
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    # boa.set_network_env(NETWORK)
    # boa.env.add_account(account_load('curve'))
    boracle, voracle, verifier, d_verifier = deploy()
    user = "0x52f541764E6e90eeBc5c21Ff570De0e2D63766B6"
    simulate(user, boracle, voracle, verifier)
