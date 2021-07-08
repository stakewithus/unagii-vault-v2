# @version 0.2.12

from vyper.interfaces import ERC20

token: public(address)
debt: public(uint256)

## test helpers ##
maxBorrow: public(uint256)
maxRepay: public(uint256)
gain: public(uint256)
loss: public(uint256)


@external
def __init__(token: address):
    self.token = token
    self.maxBorrow = MAX_UINT256
    self.maxRepay = MAX_UINT256


@external
@payable
def __default__():
    pass


@internal
def _sendEth(to: address, amount: uint256):
    raw_call(to, b"", value=amount)


@external
def borrow(_amount: uint256) -> uint256:
    amount: uint256 = min(_amount, self.maxBorrow)
    self._sendEth(msg.sender, amount)
    return amount


@external
@payable
def repay(_amount: uint256) -> uint256:
    amount: uint256 = min(_amount, self.maxRepay)
    assert amount == msg.value, "amount != msg.value"
    return amount


@external
@payable
def report(gain: uint256, loss: uint256):
    assert gain == msg.value, "gain != msg.value"
    self.gain = gain
    self.loss = loss


## test helpers ##
@external
def setToken(token: address):
    self.token = token


@external
def setDebt(debt: uint256):
    self.debt = debt


@external
def setMaxBorrow(maxBorrow: uint256):
    self.maxBorrow = maxBorrow


@external
def setMaxRepay(maxRepay: uint256):
    self.maxRepay = maxRepay
