# @version ^0.2.15

"""
used for unit testing EthVault.vy
"""


ETH: constant(address) = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE


timeLock: public(address)
nextTimeLock: public(address)
admin: public(address)
vault: public(address)
token: public(address)


@external
def __init__(vault: address):
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.vault = vault
    self.token = ETH


@external
@payable
def __default__():
    pass


@internal
@view
def _totalAssets() -> uint256:
    return self.balance


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


### test helpers ###
@external
def _setVault_(vault: address):
    assert msg.sender == self.timeLock, "!time lock"
    self.vault = vault


@external
def _setToken_(token: address):
    self.token = token


@external
def _burn_(amount: uint256):
    send(ZERO_ADDRESS, amount)