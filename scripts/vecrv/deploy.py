import json
import os
from getpass import getpass

import boa
import boa_solidity
from eth_account import account
from vyper.utils import keccak256
from hexbytes import HexBytes
from proof import (
    generate_balance_proof,
    generate_total_proof,
)
from web3 import Web3

NETWORK = "https://rpc.frax.com"
DEPLOYER = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"

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


def get_delegate_bytecode(deployer):
    contract = boa.load_partial("contracts/vecrv/VecrvDelegate.vy")
    args = boa.util.abi.abi_encode("(address)", (deployer,))
    bytecode = contract.compiler_data.bytecode + args
    return bytecode


def delegate_address_mine_cmd(deployer=DEPLOYER):
    pattern = "de1e6a7eXXXXXXXXXXXXXXXXXXXXXXXXXXX4ec84"
    bytecode = get_delegate_bytecode(deployer)
    code_hash = keccak256(bytecode).hex()
    cmd = f"""# Clone and build the miner:
    git clone https://github.com/HrikB/createXcrunch.git
    cd createXcrunch
    cargo build --release

    # Run the miner:
    ./target/release/createxcrunch create2 \\
        --caller {deployer} \\
        --code-hash {code_hash} \\
        --output {pattern[0:10]}.txt \\
        --matching {pattern}
        """
    print(cmd)


def deploy_delegate(deployer=DEPLOYER):
    createx = boa.from_etherscan(
        "0xba5Ed099633D3B313e4D5F7bdc1305d3c28ba5Ed",
        "CreateX",
        api_key=os.environ["ETHERSCAN_API_KEY"],
    )
    salt = bytes.fromhex("71f718d3e4d1449d1502a6a7595eb84ebccb16830035e01cd7b7b2fd03b8d49e")
    delegate_address = createx.deployCreate2(salt, get_delegate_bytecode(deployer))
    print(f"Deployed at {delegate_address}")


def deploy():
    boracle = boa.load_partial("contracts/blockhash/OptimismBlockHashOracle.vy").at(
        "0xeB896fB7D1AaE921d586B0E5a037496aFd3E2412"
    )
    voracle = boa.load_partial("contracts/vecrv/VecrvOracle.vy").deploy()

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


def verify(user, boracle, verifier, apply=False):
    if apply:
        number = boracle.apply()
        print(f"Applied block: {number}, {boracle.get_block_hash(number).hex()}")
    else:
        l1_block = boa.from_etherscan(
            "0x4200000000000000000000000000000000000015",
            "L1Block",
            uri="https://api-optimistic.etherscan.io/api",
            api_key=os.environ["OPTIMISTIC_ETHERSCAN_TOKEN"],
        )
        number = l1_block.number()

    proofs = generate_balance_proof(user, eth_web3, number, log=True)
    verifier.verifyBalanceByBlockHash(user, HexBytes(proofs[0]), HexBytes(proofs[1]))
    print("Sibmitted proof")


def verify_total(boracle, verifier):
    number = boracle.apply()
    print(f"Applied block: {number}, {boracle.get_block_hash(number).hex()}")

    proofs = generate_total_proof(eth_web3, number, log=True)
    verifier.verifyTotalByBlockHash(HexBytes(proofs[0]), HexBytes(proofs[1]))
    print("Sibmitted proof")


def simulate(user, boracle, voracle, verifier):
    print(
        f"Initial balance: {voracle.balanceOf(user) / 10**18:.2f} / {voracle.totalSupply() / 10**18:.2f}"
    )
    verify(user, boracle, verifier)
    print(
        f"Balance just after: {voracle.balanceOf(user) / 10**18:.2f} / {voracle.totalSupply() / 10**18:.2f}"
    )
    locked = voracle.locked(user)
    print(f"Locked balance: {locked[0] / 10**18:.2f} until {locked[1]}")
    already = 0
    for i in [1, 2, 5, 10, 60, 3600, 10 * 3600, 86400, 7 * 86400]:
        boa.env.time_travel(seconds=i - already)
        already = i
        print(
            f"Balance after {i: 8} sec: {voracle.balanceOf(user) / 10**18:.2f} / {voracle.totalSupply() / 10**18:.2f}"
        )

    print("Verifying total")
    verify(user, boracle, verifier)


def account_load(fname):
    path = os.path.expanduser(os.path.join("~", ".brownie", "accounts", fname + ".json"))
    with open(path, "r") as f:
        pkey = account.decode_keyfile_json(json.load(f), getpass())
        return account.Account.from_key(pkey)


if __name__ == "__main__":
    boa.fork(NETWORK, block_identifier="latest")
    boa.env.eoa = DEPLOYER
    # boa.set_network_env(NETWORK)
    # boa.env.add_account(account_load('curve'))
    # deploy_delegate()
    boracle, voracle, verifier, d_verifier = deploy()
    simulate("0x989AEb4d175e16225E39E87d0D97A3360524AD80", boracle, voracle, verifier)
