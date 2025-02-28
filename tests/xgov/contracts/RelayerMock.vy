# pragma version 0.4.0

flag Agent:
    OWNERSHIP
    PARAMETER
    EMERGENCY


struct Message:
    target: address
    data: Bytes[MAX_BYTES]


MAX_BYTES: constant(uint256) = 1024
MAX_MESSAGES: constant(uint256) = 8

OWNERSHIP_AGENT: public(address)
PARAMETER_AGENT: public(address)
EMERGENCY_AGENT: public(address)

agent: public(Agent)
_messages: public(DynArray[Message, MAX_MESSAGES])


@external
def relay(_agent: Agent, _messages: DynArray[Message, MAX_MESSAGES]):
    self.agent = _agent
    self._messages = _messages

    self.OWNERSHIP_AGENT = msg.sender
    self.PARAMETER_AGENT = msg.sender
    self.EMERGENCY_AGENT = msg.sender


@external
def set_messenger(_messenger: address):
    pass


@external
def messages() -> DynArray[Message, MAX_MESSAGES]:
    return self._messages


@external
def renew_values():
    self.agent = empty(Agent)
    self._messages = []
