# @version 0.2.15

from vyper.interfaces import ERC20


interface TestToken:
    def burn(_from: address, amount: uint256): nonpayable


vault: public(address)
token: public(ERC20)

# test helper
loss: public(uint256)


@external
def __init__(vault: address, token: address):
    self.vault = vault
    self.token = ERC20(token)
    self.token.approve(vault, MAX_UINT256)


@external
def withdraw(amount: uint256) -> uint256:
    loss: uint256 = min(self.token.balanceOf(self), self.loss)
    if loss > 0:
        TestToken(self.token.address).burn(self, loss)

    self.token.transfer(self.vault, min(amount, self.token.balanceOf(self)))

    return loss


### test helpers ###
@external
def setVault(vault: address):
    self.vault = vault


@external
def setToken(token: address):
    self.token = ERC20(token)


@external
def setLoss(loss: uint256):
    self.loss = loss
