# @version 0.2.12

from vyper.interfaces import ERC20

token: public(ERC20)

## test helpers ##
available: public(uint256)

@external
def __init__(token: address):
    self.token = ERC20(token)
    self.available = MAX_UINT256


@external
def borrow(_amount: uint256) -> uint256:
    amount: uint256 = min(_amount, self.available)
    self.token.transfer(msg.sender, amount)
    return amount


## test helpers ##
@external
def setToken(token: address):
    self.token = ERC20(token)


@external
def setAvailable(available: uint256):
    self.available = available
