# @version 0.2.15

from vyper.interfaces import ERC20

ETH: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE

token: public(address)

## test helpers ##
maxBorrow: public(uint256)
maxRepay: public(uint256)
gain: public(uint256)
loss: public(uint256)


@external
def __init__():
    self.token = ETH
    self.maxBorrow = MAX_UINT256
    self.maxRepay = MAX_UINT256


@external
@payable
def __default__():
    pass


@external
def borrow(_amount: uint256) -> uint256:
    send(msg.sender, _amount)
    return _amount


@external
@payable
def repay():
    pass


## test helpers ##
@external
def _setToken_(token: address):
    self.token = token


@external
def _setMaxBorrow_(maxBorrow: uint256):
    self.maxBorrow = maxBorrow


@external
def _setMaxRepay_(maxRepay: uint256):
    self.maxRepay = maxRepay


@external
def _burn_(amount: uint256):
    send(ZERO_ADDRESS, amount)