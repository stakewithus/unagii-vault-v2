# @version ^0.2.12

from vyper.interfaces import ERC20


interface FundManager:
    def borrow(amount: uint256) -> uint256: nonpayable
    def repay(amount: uint256) -> uint256: payable
    def report(gain: uint256, loss: uint256): payable
    def getDebt(strategy: address) -> uint256: view


interface Strategy:
    def fundManager() -> address: view


timeLock: public(address)
nextTimeLock: public(address)
admin: public(address)
worker: public(address)
fundManager: public(FundManager)
token: public(address)

# test helpers
loss: public(uint256)
gain: public(uint256)


@external
def __init__(fundManager: address, token: address):
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.worker = msg.sender
    self.fundManager = FundManager(fundManager)
    self.token = token


@external
@payable
def __default__():
    pass


@internal
def _sendEth(to: address, amount: uint256):
    raw_call(to, b"", value=amount)


@external
def setNextTimeLock(nextTimeLock: address):
    assert msg.sender == self.timeLock, "!time lock"
    self.nextTimeLock = nextTimeLock


@external
def acceptTimeLock():
    assert msg.sender == self.nextTimeLock, "!next time lock"
    self.nextTimeLock = ZERO_ADDRESS
    self.timeLock = msg.sender


@internal
@view
def _totalAssets() -> uint256:
    return self.balance + self.gain


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


@external
def setFundManager(fundManager: address):
    assert msg.sender == self.timeLock, "!time lock"
    self.fundManager = FundManager(fundManager)


@external
def deposit(amount: uint256, _min: uint256):
    assert msg.sender in [self.admin, self.worker], "!auth"
    borrowed: uint256 = self.fundManager.borrow(amount)
    assert borrowed >= _min, "borrowed < min"
    # code to deposit into external DeFi here...


# call report after this tx to report any loss
@external
def repay(amount: uint256, _min: uint256):
    assert msg.sender in [self.admin, self.worker], "!auth"
    # code to withdraw from external DeFi here...
    repaid: uint256 = self.fundManager.repay(amount, value=amount)
    assert repaid >= _min, "repaid < min"


@external
def withdraw(amount: uint256) -> uint256:
    assert msg.sender == self.fundManager.address, "!fund manager"

    loss: uint256 = min(self.balance, self.loss)
    if loss > 0:
        self._sendEth(ZERO_ADDRESS, loss)

    self._sendEth(self.fundManager.address, min(amount, self.balance))

    return loss


@external
def harvest():
    pass


@external
def skim():
    # withdraw profit from external DeFi
    pass


# _min, _max to protect against price manipulation
@external
def report(_min: uint256, _max: uint256):
    assert msg.sender in [self.admin, self.worker], "!auth"

    total: uint256 = self._totalAssets()
    assert total >= _min and total <= _max, "total not in range"

    gain: uint256 = 0
    loss: uint256 = 0
    debt: uint256 = self.fundManager.getDebt(self)

    if total > debt:
        gain = min(total - debt, self.balance)
    else:
        loss = debt - total

    if gain > 0 or loss > 0:
        self.fundManager.report(gain, loss, value=gain)


@external
def migrate(newStrategy: address):
    assert msg.sender == self.fundManager.address, "!fund manager"
    assert (
        Strategy(newStrategy).fundManager() == self.fundManager.address
    ), "new strategy fund manager != fund manager"

    # should be approve / transfer for real strategies
    self._sendEth(newStrategy, self.balance)


### test helpers ###
@external
def setToken(token: address):
    self.token = token


@external
def setLoss(loss: uint256):
    self.loss = loss


@external
def setGain(gain: uint256):
    self.gain = gain


@external
def burn(amount: uint256):
    send(ZERO_ADDRESS, amount)
