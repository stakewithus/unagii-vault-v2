# @version ^0.2.12

from vyper.interfaces import ERC20


interface FundManager:
    def borrow(amount: uint256) -> uint256: nonpayable
    def repay(amount: uint256) -> uint256: nonpayable
    def report(gain: uint256, loss: uint256): nonpayable
    def getDebt(strategy: address) -> uint256: view


interface TestToken:
    def burn(_from: address, amount: uint256):
        nonpayable


admin: public(address)
worker: public(address)
fundManager: public(FundManager)
token: public(ERC20)

# test helpers
loss: public(uint256)
gain: public(uint256)


@external
def __init__(fundManager: address, token: address):
    self.admin = msg.sender
    self.worker = msg.sender
    self.fundManager = FundManager(fundManager)
    self.token = ERC20(token)


@internal
@view
def _totalAssets() -> uint256:
    return self.token.balanceOf(self) + self.gain


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


@external
def deposit(amount: uint256):
    assert msg.sender in [self.admin, self.worker], "!auth"
    self.fundManager.borrow(amount)
    # code to deposit into external DeFi here...


# TODO: return loss?
@external
def repay(amount: uint256):
    assert msg.sender in [self.admin, self.worker], "!auth"
    # code to withdraw from external DeFi here...
    self.token.approve(self.fundManager.address, amount)
    self.fundManager.repay(amount)


@external
def withdraw(amount: uint256) -> uint256:
    assert msg.sender == self.fundManager.address, "!fund manager"

    self.token.approve(msg.sender, amount)

    loss: uint256 = min(amount, self.loss)

    self.token.transfer(self.fundManager.address, amount - loss)
    if loss > 0:
        TestToken(self.token.address).burn(self, loss)

    return loss


@external
def harvest():
    pass


@external
def report():
    total: uint256 = self._totalAssets()
    gain: uint256 = 0
    loss: uint256 = 0
    debt: uint256 = self.fundManager.getDebt(self)

    if total > debt:
        gain = min(total - debt, self.token.balanceOf(self))
        if gain > 0:
            self.token.approve(self.fundManager.address, gain)
    else:
        loss = debt - loss

    if gain > 0 or loss > 0:
        self.fundManager.report(gain, loss)


### test helpers ###
@external
def setFundManager(fundManager: address):
    self.fundManager = FundManager(fundManager)


@external
def setToken(token: address):
    self.token = ERC20(token)


@external
def setLoss(loss: uint256):
    self.loss = loss


@external
def setGain(gain: uint256):
    self.gain = gain
