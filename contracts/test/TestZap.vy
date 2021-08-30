# @version 0.2.15


from vyper.interfaces import ERC20


interface Vault:
    def deposit(amount: uint256, _min: uint256) -> uint256: nonpayable
    def withdraw(shares: uint256, _min: uint256) -> uint256: nonpayable


token: public(ERC20)
uToken: public(ERC20)
vault: public(Vault)


@external
def __init__(token: address, uToken: address, vault: address):
    self.token = ERC20(token)
    self.uToken = ERC20(uToken)
    self.vault = Vault(vault)

    self.token.approve(vault, MAX_UINT256)


@external
def zapIn(amount: uint256):
    self.token.transferFrom(msg.sender, self, amount)
    shares: uint256 = self.vault.deposit(amount, 0)
    self.uToken.transfer(msg.sender, shares)


@external
def zapOut(shares: uint256):
    self.uToken.transferFrom(msg.sender, self, shares)
    amount: uint256 = self.vault.withdraw(shares, 0)
    self.token.transfer(msg.sender, amount)
