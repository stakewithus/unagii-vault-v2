# @version 0.2.12

event Transfer:
    sender: indexed(address)
    recipient: indexed(address)
    amount: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    amount: uint256


name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowances: HashMap[address, HashMap[address, uint256]]
totalSupply: public(uint256)


@external
def __init__(name: String[64], symbol: String[32], decimals: uint256):
    self.name = name
    self.symbol = symbol
    self.decimals = decimals


@external
@view
def allowance(owner : address, spender : address) -> uint256:
    return self.allowances[owner][spender]


@external
def transfer(_to : address, amount : uint256) -> bool:
    self.balanceOf[msg.sender] -= amount
    self.balanceOf[_to] += amount
    log Transfer(msg.sender, _to, amount)
    return True


@external
def transferFrom(_from : address, _to : address, amount : uint256) -> bool:
    self.balanceOf[_from] -= amount
    self.balanceOf[_to] += amount
    self.allowances[_from][msg.sender] -= amount
    log Transfer(_from, _to, amount)
    return True


@external
def approve(spender : address, amount : uint256) -> bool:
    self.allowances[msg.sender][spender] = amount
    log Approval(msg.sender, spender, amount)
    return True


@external
def _mint_(_to: address, amount: uint256):
    self.totalSupply += amount
    self.balanceOf[_to] += amount
    log Transfer(ZERO_ADDRESS, _to, amount)


@external
def _burn_(_from: address, amount: uint256):
    self.totalSupply -= amount
    self.balanceOf[_from] -= amount
    log Transfer(_from, ZERO_ADDRESS, amount)