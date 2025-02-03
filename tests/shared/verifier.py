import logging

import boa

from trie import HexaryTrie
import eth_utils
import eth_abi
import rlp
from eth.vm.forks.cancun.blocks import CancunBlockHeader, BlockHeaderAPI
from eth.constants import BLANK_ROOT_HASH
from eth.db.journal import DELETE_WRAPPED, REVERT_TO_WRAPPED
from eth.rlp.accounts import Account
from typing import cast


REVERT_MESSAGE = "Revert updating parameters to storage"


def _update_without_persist(account_db, query):
    for _address, store in account_db._dirty_account_stores():
        store.make_storage_root()

    for address, storage_root in account_db._get_changed_roots():
        if account_db.account_exists(address) or storage_root != BLANK_ROOT_HASH:
            account_db.logger.debug2(
                f"Updating account 0x{address.hex()} to storage root "
                f"0x{storage_root.hex()}",
            )
            account_db._set_storage_root(address, storage_root)

    journal_db = account_db._journaldb
    journal_data = journal_db._journal._current_values
    for key, value in journal_data.items():
        try:
            if value is DELETE_WRAPPED:
                del journal_db._wrapped_db[key]
            elif value is REVERT_TO_WRAPPED:
                pass
            else:
                journal_db._wrapped_db[key] = cast(bytes, value)
        except Exception:
            journal_db._reapply_checkpoint_to_journal(journal_data)
            raise

    new_state_root = None
    diff = account_db._journaltrie.diff()

    # In addition to squashing (which is redundant here), this context manager
    # causes an atomic commit of the changes, so exceptions will revert the trie
    logger = logging.getLogger("eth.db.AtomicDBWriteBatch")
    logger_was_disabled = logger.disabled
    try:
        # First apply account changes
        with account_db._trie.squash_changes() as memory_trie:
            account_db._apply_account_diff_without_proof(diff, memory_trie)

            # Apply storage changes
            with account_db._raw_store_db.atomic_batch() as write_batch:
                for address, store in account_db._dirty_account_stores():
                    account_db._validate_flushed_storage(address, store)
                    # store.persist(write_batch)
                    if store._storage_lookup.has_changed_root:
                        # store._storage_lookup.commit_to(write_batch)
                        diff = store._storage_lookup._trie_nodes_batch.diff()
                        diff.apply_to(write_batch, True)

                # Save resulted state root
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
                    account = rlp.decode(memory_trie.get(address_bytes), sedes=Account)
                    storage_trie = HexaryTrie(
                        write_batch,
                        account.storage_root,
                    )

                    storage_proof = []
                    for slot in slots:
                        slot_hash = eth_utils.keccak(eth_abi.encode(["uint256"], [slot]))  # Correctly hash the slot
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
                logger.disabled = True
                raise Exception(REVERT_MESSAGE)
    except Exception as e:
        logger.disabled = logger_was_disabled
        assert str(e) == REVERT_MESSAGE
        pass
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
