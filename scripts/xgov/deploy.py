import json
import os
from getpass import getpass
from types import SimpleNamespace

import boa
import boa_solidity
from boa.contracts.vyper.vyper_contract import VyperFunction, generate_blueprint_bytecode
from eth_abi import abi
from eth_account import account
from proof import generate_message_digest_proof
from web3 import Web3

AGENT = 1  # ALTER
CHAIN_ID = 1284  # ALTER
NONCE = 0  # ALTER
MESSAGES = [("0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683", bytes("test", "utf-8"))]  # ALTER
FORCE_EVM = "paris"
CREATE_X_ADDRESS = os.environ.get("CREATE_X_ADDRESS", "0xba5Ed099633D3B313e4D5F7bdc1305d3c28ba5Ed")
CREATE3_LABELS = {
    "agent": "xgov.agent.blueprint",
    "relayer": "xgov.xyz_relayer",
    "vault": "xgov.vault",
    "verifier": "xgov.message_digest_verifier",
}
CREATE3_SALTS = {
    CREATE3_LABELS["agent"]: "0x71f718d3e4d1449d1502a6a7595eb84ebccb1683000000000000000000c29039",
    CREATE3_LABELS["relayer"]: "0x71f718d3e4d1449d1502a6a7595eb84ebccb16830000000000000000006b58b7",
    CREATE3_LABELS["vault"]: "0x71f718d3e4d1449d1502a6a7595eb84ebccb1683000000000000000000a73635",
    CREATE3_LABELS[
        "verifier"
    ]: "0x71f718d3e4d1449d1502a6a7595eb84ebccb16830000000000000000013f9829",
}
VYPER_COMPILER_ARGS = {"evm_version": FORCE_EVM}
SOLIDITY_COMPILER_ARGS = {
    "solc_version": "0.8.18",
    "optimize": True,
    "optimize_runs": 200,
    "evm_version": FORCE_EVM,
    "import_remappings": "hamdiallam/Solidity-RLP@2.0.7=/Users/romanagureev/.brownie/packages/hamdiallam/Solidity-RLP@2.0.7",
}
ETH_NETWORK = (
    f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_API_KEY']}"
)
NETWORK = "https://rpc.api.moonbeam.network"

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


def load_vyper(path, force_evm=FORCE_EVM):
    return boa.load_partial(path, compiler_args={"evm_version": force_evm})


def load_solidity(path):
    return boa_solidity.load_partial_solc(path, compiler_args=SOLIDITY_COMPILER_ARGS)


def createx():
    return boa.loads_abi(
        """[
            {
                "inputs": [
                    {"internalType": "bytes32", "name": "salt", "type": "bytes32"},
                    {"internalType": "bytes", "name": "initCode", "type": "bytes"}
                ],
                "name": "deployCreate3",
                "outputs": [
                    {"internalType": "address", "name": "newContract", "type": "address"}
                ],
                "stateMutability": "payable",
                "type": "function"
            }
        ]""",
        name="CreateX",
    ).at(CREATE_X_ADDRESS)


def create3_salt(label):
    try:
        return bytes.fromhex(CREATE3_SALTS[label].removeprefix("0x"))
    except KeyError as exc:
        raise KeyError(f"No CREATE3 salt configured for label: {label}") from exc


def deploy_create3(initcode, label):
    salt = create3_salt(label)
    address = createx().deployCreate3(salt, initcode)
    print(f"Create3 {label}: {address} (salt={salt.hex()})")
    return address


def vyper_initcode(deployer, *args):
    encoded_args = b""

    # `boa.load_partial()` returns `VVMDeployer` when the contract pragma does not
    # match the locally installed Vyper. In that case constructor encoding is only
    # available via the ABI-level `constructor` helper.
    if hasattr(deployer, "constructor"):
        constructor = deployer.constructor
        if constructor is not None:
            encoded_args = constructor.prepare_calldata(*args)
        elif args:
            raise ValueError(f"No constructor, but args were provided: {args}")
        return deployer.bytecode + encoded_args

    init_fn = deployer.compiler_data.global_ctx.init_function
    if init_fn is not None:
        dummy_contract = SimpleNamespace(env=boa.env, compiler_data=deployer.compiler_data)
        encoded_args = VyperFunction(init_fn.decl_node, dummy_contract).prepare_calldata(*args)
    return deployer.compiler_data.bytecode + encoded_args


def deploy_vyper_create3(deployer, label, *args, blueprint=False):
    if blueprint:
        address = deploy_create3(generate_blueprint_bytecode(deployer.bytecode), label)
        return SimpleNamespace(address=address)

    return deployer.at(deploy_create3(vyper_initcode(deployer, *args), label))


def deploy_solidity_create3(deployer, label, *args):
    if len(args) != len(deployer.types):
        raise ValueError(f"Expected {len(deployer.types)} arguments, got {len(args)}")

    encoded_args = abi.encode(deployer.types, [getattr(arg, "address", arg) for arg in args])
    return deployer.at(deploy_create3(deployer.bytecode + encoded_args, label))


def deploy(boracle):
    agent = deploy_vyper_create3(
        load_vyper(
            "tests/xgov/contracts/curve-xgov/contracts/Agent.vy",
        ),
        CREATE3_LABELS["agent"],
        blueprint=True,
    )
    # agent = boa.load_partial("tests/xgov/contracts/curve-xgov/contracts/Agent.vy").at("0x9056184de3cC7963bc62fA00778d7bd9DB7Aa9e7")
    relayer = deploy_vyper_create3(
        load_vyper(
            "tests/xgov/contracts/curve-xgov/contracts/xyz/XYZRelayer.vy",
        ),
        CREATE3_LABELS["relayer"],
        agent,
        boa.env.eoa,
    )
    # relayer = boa.load_partial("tests/xgov/contracts/curve-xgov/contracts/xyz/XYZRelayer.vy").at("0x900e54EAfE5f05683907a22A0f532D5C25302E1E")
    vault = deploy_vyper_create3(
        load_vyper("tests/xgov/contracts/curve-xgov/contracts/Vault.vy"),
        CREATE3_LABELS["vault"],
        relayer.OWNERSHIP_AGENT(),
    )
    # vault = boa.load_partial("tests/xgov/contracts/curve-xgov/contracts/Vault.vy").at("0x902ABb969f510C64210769811DFBAA943dF7fA17")

    verifier = deploy_solidity_create3(
        load_solidity("contracts/xgov/verifiers/MessageDigestVerifier.sol"),
        CREATE3_LABELS["verifier"],
        boracle,
        relayer.address,
    )

    relayer.relay(
        1,  # owner
        [(relayer.address, relayer.set_messenger.prepare_calldata(verifier))],
    )
    assert relayer.messenger() == verifier.address

    print(
        f"Relayer: {relayer.address}\n"
        f"- owner: {relayer.OWNERSHIP_AGENT()}\n"
        f"- parameter: {relayer.PARAMETER_AGENT()}\n"
        f"- emergency: {relayer.EMERGENCY_AGENT()}\n"
        f"Vault: {vault.address}\n"
        "\n"
        f"Agent: {agent.address}\n"
        f"Verifier: {verifier.address}\n"
    )
    return verifier


def send_blockhash():
    boa.fork(ETH_NETWORK, block_identifier="latest")
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    # boa.set_network_env(ETH_NETWORK)
    # boa.env.add_account(account_load('curve'))

    block_num = boa.eval("block.number")
    print(f"Latest block number: {block_num}")
    sender = load_vyper("contracts/xdao/contracts/messengers/LayerZeroSender.vy").at(
        "0x49cdecc38B4CAf6a07c13558A32820333BC2aB61"
    )
    sender.transmit(block_num - 64 - 3, value=sender.quote())


def simulate(relayer, verifier):
    relayer = load_vyper("contracts/xdao/contracts/xgov/XYZRelayer.vy").at(relayer)
    with boa.env.prank(relayer.OWNERSHIP_AGENT()):
        relayer.set_messenger(verifier)
    # boa.env.time_travel(seconds=86400 * 7)

    proofs = generate_message_digest_proof(
        eth_web3, agent=AGENT, chain_id=CHAIN_ID, nonce=NONCE, block_number=21458536, log=True
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
    boa.fork(NETWORK, block_identifier="latest")
    boa.env.eoa = "0x71F718D3e4d1449D1502A6A7595eb84eBcCB1683"
    # boa.set_network_env(NETWORK)
    # boa.env.add_account(account_load("curve"))

    verifier = deploy(
        "0xb10cface698eBbEeda6Fd1aC3e1687a8a3f5c5Df",
    )
    # simulate(
    #     "0x37b6d6d425438a9f8e40C8B4c06c10560967b678",
    #     verifier,
    # )
