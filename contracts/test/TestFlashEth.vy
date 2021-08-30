# @version 0.2.15

from vyper.interfaces import ERC20


interface Vault:
    def deposit(amount: uint256, _min: uint256) -> uint256: payable
    def withdraw(shares: uint256, _min: uint256) -> uint256: nonpayable


token: public(address)
uToken: public(ERC20)
vault: public(Vault)


@external
def __init__(token: address, uToken: address, vault: address):
    self.token = token
    self.uToken = ERC20(uToken)
    self.vault = Vault(vault)


@external
@payable
def __default__():
    pass


@external
def deposit():
    bal: uint256 = self.balance
    assert bal > 0, "bal == 0"
    self.vault.deposit(bal, 0, value=bal)


@external
def withdraw():
    shares: uint256 = self.uToken.balanceOf(self)
    assert shares > 0, "shares = 0"
    self.vault.withdraw(shares, 0)


@external
def deposit_and_withdraw():
    bal: uint256 = self.balance
    assert bal > 0, "bal == 0"

    shares: uint256 = self.vault.deposit(bal, 0, value=bal)
    self.vault.withdraw(shares, 0)


@external
def withdraw_and_deposit():
    shares: uint256 = self.uToken.balanceOf(self)
    assert shares > 0, "shares = 0"

    amount: uint256 = self.vault.withdraw(shares, 0)
    self.vault.deposit(amount, 0, value=amount)
