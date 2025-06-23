import eth_abi
import rlp
import web3
from hexbytes import HexBytes

BLOCK_NUMBER = 18578883  # ALTER
VOTING_ESCROW = "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2"

VERIFIER = ""  # ALTER
VECRV_DELEGATE = "0xde1e6A7E8297076f070E857130E593107A0E0cF5"
SLOPE_CHANGES_NUM = 24  # 6 months

WEEK = 7 * 86400

# https://github.com/ethereum/go-ethereum/blob/master/core/types/block.go#L69
BLOCK_HEADER = (
    "parentHash",
    "sha3Uncles",
    "miner",
    "stateRoot",
    "transactionsRoot",
    "receiptsRoot",
    "logsBloom",
    "difficulty",
    "number",
    "gasLimit",
    "gasUsed",
    "timestamp",
    "extraData",
    "mixHash",
    "nonce",
    # New fields are ignored in legacy headers
    # London
    "baseFeePerGas",  # added by EIP-1559
    # Shanghai
    "withdrawalsRoot",  # added by EIP-4895
    # Cancun
    "blobGasUsed",  # added by EIP-4844
    "excessBlobGas",  # added by EIP-4844
    "parentBeaconBlockRoot",  # added by EIP-4788
    # Prague
    "requestsHash",  # added by EIP-7685
)


def serialize_block(block):
    block_header = [
        (
            HexBytes("0x")
            if (isinstance((v := block[k]), int) and v == 0) or v == "0x0"
            else HexBytes(block[k])
        )
        for k in BLOCK_HEADER
        if k in block
    ]
    block_header[14] = HexBytes("0x0000000000000000")  # nonce
    return rlp.encode(block_header)


def serialize_proofs(proofs, encode=True):
    account_proof = list(map(rlp.decode, map(HexBytes, proofs["accountProof"])))
    storage_proofs = [
        list(map(rlp.decode, map(HexBytes, proof["proof"]))) for proof in proofs["storageProof"]
    ]
    if encode:
        return rlp.encode([account_proof, *storage_proofs])
    else:
        return [account_proof, *storage_proofs]


def hashmap(slot, value, type) -> int:
    if isinstance(slot, HexBytes):
        slot = int(slot.hex(), 16)
    return int(
        web3.Web3.keccak(eth_abi.encode([f"(uint256,{type})"], [[slot, value]])).hex(),
        16,
    )


def keccak256(value: int) -> int:
    return int(web3.Web3.keccak(eth_abi.encode(["uint256"], [value])).hex(), 16)


def array(slot, index) -> int:
    if isinstance(slot, HexBytes):
        slot = int(slot.hex(), 16)
    return keccak256(slot) + index


def struct(slot) -> int:
    return keccak256(slot)


def voting_escrow_contract(eth_web3):
    return eth_web3.eth.contract(
        address=VOTING_ESCROW,
        abi=[
            {
                "name": "CommitOwnership",
                "inputs": [{"type": "address", "name": "admin", "indexed": False}],
                "anonymous": False,
                "type": "event",
            },
            {
                "name": "ApplyOwnership",
                "inputs": [{"type": "address", "name": "admin", "indexed": False}],
                "anonymous": False,
                "type": "event",
            },
            {
                "name": "Deposit",
                "inputs": [
                    {"type": "address", "name": "provider", "indexed": True},
                    {"type": "uint256", "name": "value", "indexed": False},
                    {"type": "uint256", "name": "locktime", "indexed": True},
                    {"type": "int128", "name": "type", "indexed": False},
                    {"type": "uint256", "name": "ts", "indexed": False},
                ],
                "anonymous": False,
                "type": "event",
            },
            {
                "name": "Withdraw",
                "inputs": [
                    {"type": "address", "name": "provider", "indexed": True},
                    {"type": "uint256", "name": "value", "indexed": False},
                    {"type": "uint256", "name": "ts", "indexed": False},
                ],
                "anonymous": False,
                "type": "event",
            },
            {
                "name": "Supply",
                "inputs": [
                    {"type": "uint256", "name": "prevSupply", "indexed": False},
                    {"type": "uint256", "name": "supply", "indexed": False},
                ],
                "anonymous": False,
                "type": "event",
            },
            {
                "outputs": [],
                "inputs": [
                    {"type": "address", "name": "token_addr"},
                    {"type": "string", "name": "_name"},
                    {"type": "string", "name": "_symbol"},
                    {"type": "string", "name": "_version"},
                ],
                "stateMutability": "nonpayable",
                "type": "constructor",
            },
            {
                "name": "commit_transfer_ownership",
                "outputs": [],
                "inputs": [{"type": "address", "name": "addr"}],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 37597,
            },
            {
                "name": "apply_transfer_ownership",
                "outputs": [],
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 38497,
            },
            {
                "name": "commit_smart_wallet_checker",
                "outputs": [],
                "inputs": [{"type": "address", "name": "addr"}],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 36307,
            },
            {
                "name": "apply_smart_wallet_checker",
                "outputs": [],
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 37095,
            },
            {
                "name": "get_last_user_slope",
                "outputs": [{"type": "int128", "name": ""}],
                "inputs": [{"type": "address", "name": "addr"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 2569,
            },
            {
                "name": "user_point_history__ts",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [
                    {"type": "address", "name": "_addr"},
                    {"type": "uint256", "name": "_idx"},
                ],
                "stateMutability": "view",
                "type": "function",
                "gas": 1672,
            },
            {
                "name": "locked__end",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "address", "name": "_addr"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 1593,
            },
            {
                "name": "checkpoint",
                "outputs": [],
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 37052342,
            },
            {
                "name": "deposit_for",
                "outputs": [],
                "inputs": [
                    {"type": "address", "name": "_addr"},
                    {"type": "uint256", "name": "_value"},
                ],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 74279891,
            },
            {
                "name": "create_lock",
                "outputs": [],
                "inputs": [
                    {"type": "uint256", "name": "_value"},
                    {"type": "uint256", "name": "_unlock_time"},
                ],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 74281465,
            },
            {
                "name": "increase_amount",
                "outputs": [],
                "inputs": [{"type": "uint256", "name": "_value"}],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 74280830,
            },
            {
                "name": "increase_unlock_time",
                "outputs": [],
                "inputs": [{"type": "uint256", "name": "_unlock_time"}],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 74281578,
            },
            {
                "name": "withdraw",
                "outputs": [],
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 37223566,
            },
            {
                "name": "balanceOf",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "address", "name": "addr"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "name": "balanceOf",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [
                    {"type": "address", "name": "addr"},
                    {"type": "uint256", "name": "_t"},
                ],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "name": "balanceOfAt",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [
                    {"type": "address", "name": "addr"},
                    {"type": "uint256", "name": "_block"},
                ],
                "stateMutability": "view",
                "type": "function",
                "gas": 514333,
            },
            {
                "name": "totalSupply",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "name": "totalSupply",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "uint256", "name": "t"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "name": "totalSupplyAt",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "uint256", "name": "_block"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 812560,
            },
            {
                "name": "changeController",
                "outputs": [],
                "inputs": [{"type": "address", "name": "_newController"}],
                "stateMutability": "nonpayable",
                "type": "function",
                "gas": 36907,
            },
            {
                "name": "token",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 1841,
            },
            {
                "name": "supply",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 1871,
            },
            {
                "name": "locked",
                "outputs": [
                    {"type": "int128", "name": "amount"},
                    {"type": "uint256", "name": "end"},
                ],
                "inputs": [{"type": "address", "name": "arg0"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 3359,
            },
            {
                "name": "epoch",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 1931,
            },
            {
                "name": "point_history",
                "outputs": [
                    {"type": "int128", "name": "bias"},
                    {"type": "int128", "name": "slope"},
                    {"type": "uint256", "name": "ts"},
                    {"type": "uint256", "name": "blk"},
                ],
                "inputs": [{"type": "uint256", "name": "arg0"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 5550,
            },
            {
                "name": "user_point_history",
                "outputs": [
                    {"type": "int128", "name": "bias"},
                    {"type": "int128", "name": "slope"},
                    {"type": "uint256", "name": "ts"},
                    {"type": "uint256", "name": "blk"},
                ],
                "inputs": [
                    {"type": "address", "name": "arg0"},
                    {"type": "uint256", "name": "arg1"},
                ],
                "stateMutability": "view",
                "type": "function",
                "gas": 6079,
            },
            {
                "name": "user_point_epoch",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [{"type": "address", "name": "arg0"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 2175,
            },
            {
                "name": "slope_changes",
                "outputs": [{"type": "int128", "name": ""}],
                "inputs": [{"type": "uint256", "name": "arg0"}],
                "stateMutability": "view",
                "type": "function",
                "gas": 2166,
            },
            {
                "name": "controller",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2081,
            },
            {
                "name": "transfersEnabled",
                "outputs": [{"type": "bool", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2111,
            },
            {
                "name": "name",
                "outputs": [{"type": "string", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 8543,
            },
            {
                "name": "symbol",
                "outputs": [{"type": "string", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 7596,
            },
            {
                "name": "version",
                "outputs": [{"type": "string", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 7626,
            },
            {
                "name": "decimals",
                "outputs": [{"type": "uint256", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2231,
            },
            {
                "name": "future_smart_wallet_checker",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2261,
            },
            {
                "name": "smart_wallet_checker",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2291,
            },
            {
                "name": "admin",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2321,
            },
            {
                "name": "future_admin",
                "outputs": [{"type": "address", "name": ""}],
                "inputs": [],
                "stateMutability": "view",
                "type": "function",
                "gas": 2351,
            },
        ],
    )


def get_balance_slots(user, eth_web3):
    ve = voting_escrow_contract(eth_web3)

    user_epoch = ve.functions.user_point_epoch(user).call()
    user_point_history_slot = struct(array(hashmap(5, user, "address"), user_epoch))

    locked_balance_slot = struct(hashmap(2, user, "address"))
    return [
        hashmap(6, user, "address"),  # user point epoch
        *(user_point_history_slot + i for i in range(4)),  # user point history
        *(locked_balance_slot + i for i in range(2)),  # locked balance
    ]


def get_total_slots(eth_web3, block, slope_changes_num=4):
    ve = voting_escrow_contract(eth_web3)

    epoch = ve.functions.epoch().call(block_identifier=block.number)
    point_history_slot = struct(array(4, epoch))

    point_history = ve.functions.point_history(epoch).call(block_identifier=block.number)
    start = WEEK + (point_history_ts := point_history[2]) // WEEK * WEEK  # noqa: F841
    return [
        3,  # epoch
        *(point_history_slot + i for i in range(4)),  # point history
        *(
            hashmap(7, start + i * WEEK, "uint256") for i in range(slope_changes_num)
        ),  # slope changes
    ]


def get_delegation_slots(chain_id, user):
    return [
        hashmap(hashmap(1, chain_id, "uint256"), user, "address"),  # delegation_from
    ]


def generate_balance_proof(user, eth_web3, block_number=BLOCK_NUMBER, log=False):
    block = eth_web3.eth.get_block(block_number)
    if log:
        print(f"Generating proof for block {block.number}, {block.hash.hex()}")
    block_header_rlp = serialize_block(block)

    total_slots = get_total_slots(eth_web3, block)
    balance_slots = get_balance_slots(user, eth_web3)
    proofs = serialize_proofs(
        eth_web3.eth.get_proof(
            VOTING_ESCROW,
            total_slots + balance_slots,
            block_number,
        ),
        encode=False,
    )
    proof_rlp = rlp.encode(
        [proofs[0], proofs[1 : 1 + len(total_slots)], proofs[1 + len(total_slots) :]]
    )

    if log:
        with open("header.txt", "w") as f:
            f.write(block_header_rlp.hex())
        with open("proof.txt", "w") as f:
            f.write(proof_rlp.hex())

    return block_header_rlp.hex(), proof_rlp.hex()


def generate_total_proof(
    eth_web3, slope_changes_num=SLOPE_CHANGES_NUM, block_number=BLOCK_NUMBER, log=False
):
    block = eth_web3.eth.get_block(block_number)
    if log:
        print(f"Generating proof for block {block.number}, {block.hash.hex()}")
    block_header_rlp = serialize_block(block)

    total_slots = get_total_slots(eth_web3, block, slope_changes_num=slope_changes_num)
    proofs = serialize_proofs(
        eth_web3.eth.get_proof(
            VOTING_ESCROW,
            total_slots,
            block_number,
        ),
        encode=False,
    )
    proof_rlp = rlp.encode([proofs[0], proofs[1:]])

    if log:
        with open("header.txt", "w") as f:
            f.write(block_header_rlp.hex())
        with open("proof.txt", "w") as f:
            f.write(proof_rlp.hex())

    return block_header_rlp.hex(), proof_rlp.hex()


def generate_delegation_proof(chain_id, user, eth_web3, block_number=BLOCK_NUMBER, log=False):
    block = eth_web3.eth.get_block(block_number)
    if log:
        print(f"Generating proof for block {block.number}, {block.hash.hex()}")
    block_header_rlp = serialize_block(block)

    proof_rlp = serialize_proofs(
        eth_web3.eth.get_proof(
            VECRV_DELEGATE,
            get_delegation_slots(chain_id, user),
            block_number,
        )
    )

    if log:
        with open("header.txt", "w") as f:
            f.write(block_header_rlp.hex())
        with open("proof.txt", "w") as f:
            f.write(proof_rlp.hex())

    return block_header_rlp.hex(), proof_rlp.hex()
