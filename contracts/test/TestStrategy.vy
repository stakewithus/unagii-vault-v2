# @version ^0.2.15

"""
used for unit testing Vault.vy
"""

from vyper.interfaces import ERC20


timeLock: public(address)
nextTimeLock: public(address)
admin: public(address)
vault: public(address)
token: public(ERC20)


@external
def __init__(vault: address, token: address):
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.vault = vault
    self.token = ERC20(token)


@internal
@view
def _totalAssets() -> uint256:
    return self.token.balanceOf(self)


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


### test helpers ###
@external
def _setVault_(vault: address):
    assert msg.sender == self.timeLock, "!time lock"

    if self.vault != ZERO_ADDRESS:
        self.token.approve(self.vault, 0)

    self.vault = vault
    self.token.approve(vault, MAX_UINT256)


@external
def _setToken_(token: address):
    self.token = ERC20(token)
