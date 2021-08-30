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
@payable
def zapIn(amount: uint256):
    assert amount == msg.value, "amount != msg.value"
    shares: uint256 = self.vault.deposit(amount, 0, value=msg.value)
    self.uToken.transfer(msg.sender, shares)


@external
def zapOut(shares: uint256):
    self.uToken.transferFrom(msg.sender, self, shares)
    amount: uint256 = self.vault.withdraw(shares, 0)
    send(msg.sender, amount)
