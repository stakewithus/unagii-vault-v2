# @version 0.2.12

from vyper.interfaces import ERC20

token: public(ERC20)


@external
def __init__(token: address):
    self.token = ERC20(token)


@external
def setToken(token: address):
    self.token = ERC20(token)
