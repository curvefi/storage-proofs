# pragma version 0.4.0

sender: public(address)
_input: public(Bytes[256])


@external
def receive_message(_input: Bytes[256]):
    self.sender = msg.sender
    self._input = _input


@external
def input() -> Bytes[256]:
    return self._input


@external
def renew_values():
    self.sender = empty(address)
    self._input = empty(Bytes[256])
