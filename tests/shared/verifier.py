import boa

from trie import HexaryTrie
from eth.db.hash_trie import HashTrie
from eth.db.storage import StorageLookup
import eth_utils
import eth_abi
import rlp
from eth.vm.forks.cancun.blocks import CancunBlockHeader, BlockHeaderAPI
from eth.db.journal import DELETE_WRAPPED, REVERT_TO_WRAPPED
from eth.rlp.accounts import Account
from typing import cast
from trie.utils.db import ScratchDB


def _update_without_persist(account_db, query):
    # Currently boa never flushes caches(`.persist()`) to have all snapshots available,
    # so db and _trie are actually empty.
    # Though, saving reference in case of future changes.
    write_batch = ScratchDB(account_db._raw_store_db.wrapped_db)
    memory_trie = HashTrie(HexaryTrie(write_batch, account_db._trie.root_hash, prune=True))

    # Skipping existing account_db._journaltrie.diff() because currently empty.

    for _address, store in account_db._dirty_account_stores():
        storage_lookup = StorageLookup(write_batch, store._storage_lookup._starting_root_hash, _address)
        journal_data = store._journal_storage._journal._current_values

        for key, value in journal_data.items():
            if value is DELETE_WRAPPED:
                del storage_lookup[key]
            elif value is REVERT_TO_WRAPPED:
                pass
            else:
                storage_lookup[key] = cast(bytes, value)

        if storage_lookup.has_changed_root:
            # Update account
            account = account_db._get_account(_address)
            rlp_account = rlp.encode(account.copy(storage_root=storage_lookup.get_changed_root()), sedes=Account)
            memory_trie[_address] = rlp_account

            # Update storage slots
            diff = storage_lookup._trie_nodes_batch.diff()
            diff.apply_to(write_batch, True)

    new_state_root = memory_trie.root_hash

    result = []
    for addr, slots in query:
        if hasattr(addr, "address"):  # is of type VyperContract
            addr = addr.address

        # Get account proof
        address_bytes = bytes.fromhex(addr[2:])  # remove "0x"
        address_hash = eth_utils.keccak(address_bytes)
        account_proof = [rlp.encode(node) for node in memory_trie.get_proof(address_hash)]

        # Get storage proofs
        account = rlp.decode(memory_trie[address_bytes], sedes=Account)
        storage_trie = HexaryTrie(
            write_batch,
            account.storage_root,
        )

        storage_proof = []
        for slot in slots:
            slot_hash = eth_utils.keccak(eth_abi.encode(["uint256"], [slot]))
            slot_proof_nodes = storage_trie.get_proof(slot_hash)
            storage_proof.append({
                "key": slot,
                "value": storage_trie.get(slot_hash),
                "proof": [rlp.encode(node) for node in slot_proof_nodes],
            })
        result.append({
            "address": addr,
            "accountProof": account_proof,
            "balance": account.balance,
            "codeHash": account.code_hash,
            "nonce": account.nonce,
            "storageHash": account.storage_root,
            "storageProof": storage_proof,
        })
    return new_state_root, result


def get_block_and_proofs(query: list) -> (BlockHeaderAPI, list):
    """
    Simulate constructing a trie of accounts and storage slots, building block header and storage proofs.
    Result is compatible with `eth_getProof`.
    Implementation is not safe and might have effects on further executions.
    :param query: [(address, slots)]
    :return: block_header, proofs
    """
    evm = boa.env.evm
    parent_header = evm.chain.get_canonical_head()

    state = evm.vm.state
    account_db = state._account_db
    state_root, proofs = _update_without_persist(account_db, query)

    block_header = CancunBlockHeader(
        difficulty=0,
        block_number=boa.env.evm.patch.block_number,
        gas_limit=2 * parent_header.gas_limit,
        timestamp=boa.env.evm.patch.timestamp,
        coinbase=parent_header.coinbase,
        parent_hash=parent_header.hash,
        state_root=state_root,
        bloom=parent_header.bloom,
        gas_used=0,  # No transactions in this block
        nonce=b'\x00\x00\x00\x00\x00\x00\x00\x00',
        base_fee_per_gas=1000000000,
    )
    return block_header, proofs
