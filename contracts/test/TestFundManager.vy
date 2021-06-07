# @version 0.2.12

from vyper.interfaces import ERC20

vault: public(address)
token: public(ERC20)


@external
def __init__(vault: address, token: address):
    self.vault = vault
    self.token = ERC20(token)


@external
def setVault(vault: address):
    self.vault = vault


@external
def setToken(token: address):
    self.token = ERC20(token)


@external
@view
def totalAssets() -> uint256:
    return self.token.balanceOf(self)
