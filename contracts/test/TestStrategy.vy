# @version ^0.2.12

fundManager: public(address)
token: public(address)


@external
def __init__(fundManager: address, token: address):
    self.fundManager = fundManager
    self.token = token

@external
def totalAssets():
    pass

@external
def deposit():
    # fundManager.borrow(MAX_UINT256)
    pass

@external
def withdraw():
    # assert only fund manager
    pass

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
    self.token = token
