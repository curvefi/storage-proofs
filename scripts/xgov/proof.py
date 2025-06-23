import eth_abi
import eth_utils
import rlp
from eth.hash import keccak256
from hexbytes import HexBytes


AGENT = 1  # ALTER
CHAIN_ID = 56  # ALTER
NONCE = 0  # ALTER

BLOCK_NUMBER = None  # ALTER: last applied block number

BROADCASTER = "0x7BA33456EC00812C6B6BB6C1C3dfF579c34CC2cc"

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
            if (isinstance((v := block.get(k, 0)), int) and v == 0) or v == "0x0"
            else HexBytes(block[k])
        )
        for k in BLOCK_HEADER
    ]
    encoded = rlp.encode(block_header)

    # Helper: https://blockhash.ardis.lu
    assert keccak256(encoded) == block["hash"], "Badly encoded block"
    return encoded


def serialize_proofs(proofs):
    account_proof = list(map(rlp.decode, map(HexBytes, proofs["accountProof"])))
    storage_proofs = [
        list(map(rlp.decode, map(HexBytes, proof["proof"]))) for proof in proofs["storageProof"]
    ]
    return rlp.encode([account_proof, *storage_proofs])


def hashmap(slot, value, type):
    if isinstance(slot, HexBytes):
        slot = int(slot.hex(), 16)
    return int.from_bytes(eth_utils.keccak(eth_abi.encode([f"(uint256,{type})"], [[slot, value]])))


def generate_message_digest_proof(
    eth_web3,
    agent=AGENT,
    chain_id=CHAIN_ID,
    nonce=NONCE,
    block_number=BLOCK_NUMBER,
    log=False,
):
    block = eth_web3.eth.get_block(block_number)
    if log:
        print(f"Generating proof for block {block.number}, {block.hash.hex()}")
    block_header_rlp = serialize_block(block)
    message_digest_slot = hashmap(
        hashmap(hashmap(8, agent, "uint256"), chain_id, "uint256"),
        nonce,
        "uint256",
    )
    deadline_slot = hashmap(
        hashmap(hashmap(9, agent, "uint256"), chain_id, "uint256"),
        nonce,
        "uint256",
    )
    proof_rlp = serialize_proofs(
        eth_web3.eth.get_proof(BROADCASTER, [message_digest_slot, deadline_slot], block_number)
    )

    with open("header.txt", "w") as f:
        f.write(block_header_rlp.hex())
    with open("proof.txt", "w") as f:
        f.write(proof_rlp.hex())

    return block_header_rlp.hex(), proof_rlp.hex()
