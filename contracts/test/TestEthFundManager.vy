# @version 0.2.12

from vyper.interfaces import ERC20


interface TestToken:
    def burn(_from: address, amount: uint256): nonpayable


vault: public(address)
token: public(address)

# test helper
loss: public(uint256)


@external
def __init__(vault: address, token: address):
    self.vault = vault
    self.token = token


@external
@payable
def __default__():
    pass


@external
def withdraw(amount: uint256) -> uint256:
    loss: uint256 = min(amount, self.loss)

    send(self.vault, amount - loss)
    if loss > 0:
        send(ZERO_ADDRESS, loss)

    return self.loss


### test helpers ###
@external
def setVault(vault: address):
    self.vault = vault


@external
def setToken(token: address):
    self.token = token


@external
def setLoss(loss: uint256):
    self.loss = loss
