import boa
import pytest

import rlp

from scripts.xgov.proof import serialize_proofs
from tests.shared.verifier import get_block_and_proofs
from tests.xgov.conftest import CHAIN_ID


@pytest.fixture(scope="module")
def message_receiver():
    return boa.load("tests/xgov/contracts/MessageReceiverMock.vy")


@pytest.fixture(scope="module")
def relayer(admin):
    with boa.env.prank(admin):
        agent = boa.load_partial(
            "tests/xgov/contracts/curve-xgov/contracts/Agent.vy"
        ).deploy_as_blueprint()
        return boa.load("tests/xgov/contracts/curve-xgov/contracts/xyz/XYZRelayer.vy", agent, admin)


@pytest.fixture(scope="module")
def generate_message(message_receiver):
    def inner(salt: int):
        input = b"00" + salt.to_bytes()
        return [(message_receiver, message_receiver.receive_message.prepare_calldata(input))], input

    return inner


def broadcast_and_get_proofs(broadcaster, admins, i, message, verifier_slots):
    with boa.env.prank(admins[i]):
        broadcaster.broadcast(CHAIN_ID, message)
    slots = verifier_slots(2**i, CHAIN_ID, 0)
    return get_block_and_proofs([(broadcaster, slots)])


@pytest.mark.parametrize("i", [0, 1, 2])
def test_relay_by_blockhash(
    verifier,
    broadcaster,
    admins,
    relayer,
    boracle,
    verifier_slots,
    message_receiver,
    generate_message,
    i,
):
    nonce = 0
    message, input = generate_message(i)
    block_header, proofs = broadcast_and_get_proofs(broadcaster, admins, i, message, verifier_slots)
    boracle._set_block_hash(block_header.block_number, block_header.hash)

    message_receiver.renew_values()
    verifier.verifyMessagesByBlockHash(
        2**i,
        message,
        rlp.encode(block_header),
        serialize_proofs(proofs[0]),
    )

    assert verifier.nonce(2**i) == nonce + 1
    assert (
        message_receiver.sender()
        == getattr(relayer, ["OWNERSHIP_AGENT", "PARAMETER_AGENT", "EMERGENCY_AGENT"][i])()
    )
    assert message_receiver.input() == input


@pytest.mark.parametrize("i", [0, 1, 2])
def test_relay_by_stateroot(
    verifier,
    broadcaster,
    admins,
    relayer,
    boracle,
    verifier_slots,
    message_receiver,
    generate_message,
    i,
):
    nonce = 0
    message, input = generate_message(i)
    block_header, proofs = broadcast_and_get_proofs(broadcaster, admins, i, message, verifier_slots)
    boracle._set_state_root(block_header.block_number, block_header.state_root)

    message_receiver.renew_values()
    verifier.verifyMessagesByStateRoot(
        2**i,
        message,
        block_header.block_number,
        serialize_proofs(proofs[0]),
    )

    assert verifier.nonce(2**i) == nonce + 1
    assert (
        message_receiver.sender()
        == getattr(relayer, ["OWNERSHIP_AGENT", "PARAMETER_AGENT", "EMERGENCY_AGENT"][i])()
    )
    assert message_receiver.input() == input
