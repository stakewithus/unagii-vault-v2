# @version ^0.2.12

vault: public(address)
token: public(address)


@external
def __init__(vault: address, token: address):
    self.vault = vault
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
def setVault(vault: address):
    self.vault = vault


@external
def setToken(token: address):
    self.token = token
