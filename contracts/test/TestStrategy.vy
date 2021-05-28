# @version ^0.2.12

vault: public(address)
token: public(address)

@external
def __init__(vault: address, token: address):
    self.vault = vault
    self.token = token

### test helpers ###
@external
def setVault(vault: address):
    self.vault = vault

@external
def setToken(token: address):
    self.token = token