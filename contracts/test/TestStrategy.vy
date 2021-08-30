# @version ^0.2.15

from vyper.interfaces import ERC20

# TODO: delete this, replace with StrategyTest.sol


timeLock: public(address)
nextTimeLock: public(address)
admin: public(address)
vault: public(address)
token: public(ERC20)

# test helpers
loss: public(uint256)
gain: public(uint256)


@external
def __init__(vault: address, token: address):
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.vault = vault
    self.token = ERC20(token)


# @external
# def setNextTimeLock(nextTimeLock: address):
#     assert msg.sender == self.timeLock, "!time lock"
#     self.nextTimeLock = nextTimeLock


# @external
# def acceptTimeLock():
#     assert msg.sender == self.nextTimeLock, "!next time lock"
#     self.nextTimeLock = ZERO_ADDRESS
#     self.timeLock = msg.sender


# @internal
# @view
# def _totalAssets() -> uint256:
#     return self.token.balanceOf(self) + self.gain


# @external
# @view
# def totalAssets() -> uint256:
#     return self._totalAssets()


@external
def setVault(vault: address):
    assert msg.sender == self.timeLock, "!time lock"

    if self.vault != ZERO_ADDRESS:
        self.token.approve(self.vault, 0)

    self.vault = vault
    self.token.approve(vault, MAX_UINT256)


# @external
# def deposit(amount: uint256, _min: uint256):
#     assert msg.sender in [self.admin, self.worker], "!auth"
#     borrowed: uint256 = self.fundManager.borrow(amount)
#     assert borrowed >= _min, "borrowed < min"
#     # code to deposit into external DeFi here...


# # call report after this tx to report any loss
# @external
# def repay(amount: uint256, _min: uint256):
#     assert msg.sender in [self.admin, self.worker], "!auth"
#     # code to withdraw from external DeFi here...
#     self.token.approve(self.fundManager.address, amount)
#     repaid: uint256 = self.fundManager.repay(amount)
#     assert repaid >= _min, "repaid < min"


# @external
# def withdraw(amount: uint256) -> uint256:
#     assert msg.sender == self.fundManager.address, "!fund manager"

#     loss: uint256 = min(self.token.balanceOf(self), self.loss)
#     if loss > 0:
#         TestToken(self.token.address).burn(self, loss)

#     _amount: uint256 = min(amount, self.token.balanceOf(self))
#     self.token.approve(msg.sender, _amount)
#     self.token.transfer(self.fundManager.address, _amount)

#     return loss


# @external
# def harvest():
#     pass


# @external
# def skim():
#     # withdraw profit from external DeFi
#     pass


# # _min, _max to protect against price manipulation
# @external
# def report(_min: uint256, _max: uint256):
#     assert msg.sender in [self.admin, self.worker], "!auth"

#     total: uint256 = self._totalAssets()
#     assert total >= _min and total <= _max, "total not in range"

#     gain: uint256 = 0
#     loss: uint256 = 0
#     debt: uint256 = self.fundManager.getDebt(self)

#     if total > debt:
#         gain = min(total - debt, self.token.balanceOf(self))
#         if gain > 0:
#             self.token.approve(self.fundManager.address, gain)
#     else:
#         loss = debt - total

#     if gain > 0 or loss > 0:
#         self.fundManager.report(gain, loss)


# @external
# def migrate(newStrategy: address):
#     assert msg.sender == self.fundManager.address, "!fund manager"
#     assert (
#         Strategy(newStrategy).fundManager() == self.fundManager.address
#     ), "new strategy fund manager != fund manager"

#     # should be approve / transfer for real strategies
#     self.token.transfer(newStrategy, self.token.balanceOf(self))


### test helpers ###
@external
def setToken(token: address):
    self.token = ERC20(token)


# @external
# def setLoss(loss: uint256):
#     self.loss = loss


# @external
# def setGain(gain: uint256):
#     self.gain = gain
