# @version 0.2.15

"""
used to test deposit / withdraw on EthVault.vy
"""


from vyper.interfaces import ERC20


interface Vault:
    def deposit(_min: uint256) -> uint256: payable
    def withdraw(shares: uint256, _min: uint256) -> uint256: nonpayable


uToken: public(ERC20)
vault: public(Vault)


@external
def __init__(uToken: address, vault: address):
    self.uToken = ERC20(uToken)
    self.vault = Vault(vault)


@external
@payable
def __default__():
    pass


@external
@payable
def zapIn():
    shares: uint256 = self.vault.deposit(0, value=msg.value)
    self.uToken.transfer(msg.sender, shares)


@external
def zapOut(shares: uint256):
    self.uToken.transferFrom(msg.sender, self, shares)
    amount: uint256 = self.vault.withdraw(shares, 0)
    send(msg.sender, amount)
