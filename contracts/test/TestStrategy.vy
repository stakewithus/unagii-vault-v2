# @version ^0.2.12

from vyper.interfaces import ERC20

fundManager: public(address)
token: public(ERC20)

interface TestToken:
    def burn(_from: address, amount: uint256): nonpayable

# test helpers
loss: public(uint256)

@external
def __init__(fundManager: address, token: address):
    self.fundManager = fundManager
    self.token = ERC20(token)

@external
def totalAssets():
    pass

@external
def deposit():
    # fundManager.borrow(MAX_UINT256)
    pass

@external
def withdraw(amount: uint256) -> uint256:
    loss: uint256 = min(amount, self.loss)

    self.token.transfer(self.fundManager, amount - loss)
    if loss > 0:
        TestToken(self.token.address).burn(self, loss)

    return loss

@external
def harvest():
    pass

@external
def repay():
    # fund manager.repay()
    pass

@external
def report():
    # fundManager.report(gain, loss)
    pass

### test helpers ###
@external
def setFundManager(fundManager: address):
    self.fundManager = fundManager


@external
def setToken(token: address):
    self.token = ERC20(token)

@external
def setLoss(loss: uint256):
    self.loss = loss