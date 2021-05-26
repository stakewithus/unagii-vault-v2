# @version 0.2.12

"""
@title Unagii Token
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

implements: ERC20

interface DetailedERC20:
    def name() -> String[42]: view
    def symbol() -> String[20]: view
    # Vyper does not support uint8
    def decimals() -> uint256: view

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

event SetNextMinter:
    minter: address

event AcceptMinter:
    minter: address

name: public(String[64])
symbol: public(String[32])
# Vyper does not support uint8
decimals: public(uint256) 
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
minter: public(address)
nextMinter: public(address)
token: public(ERC20)
lastBlock: public(HashMap[address, uint256])

# TODO: test

@external
def __init__(token: address):
    self.minter = msg.sender
    self.token = ERC20(token)
    self.name = concat("unagii_v2_", DetailedERC20(token).name())
    self.symbol = concat("u2", DetailedERC20(token).symbol())
    self.decimals = DetailedERC20(token).decimals()


@external
def setNextMinter(nextMinter: address):
    """
    @notice Set next minter
    @param nextMinter Address of next minter
    """
    assert msg.sender == self.minter, "!minter"
    assert nextMinter != self.minter, "next minter = current"
    # allow next minter = zero address (cancel next minter)
    self.nextMinter = nextMinter
    log SetNextMinter(nextMinter)


@external
def acceptMinter():
    """
    @notice Accept minter
    @dev Only `nextMinter` can claim minter 
    """
    assert msg.sender == self.nextMinter, "!next minter"
    self.minter = msg.sender
    self.nextMinter = ZERO_ADDRESS
    log AcceptMinter(msg.sender)


@internal
def _transfer(_from: address, _to: address, amount: uint256):
    assert _to not in [self, ZERO_ADDRESS], "invalid receiver"
    
    # track lastest tx
    self.lastBlock[_from] = block.number
    self.lastBlock[_to] = block.number

    self.balanceOf[_from] -= amount
    self.balanceOf[_to] += amount
    log Transfer(_from, _to, amount)


@external
def transfer(_to: address, amount: uint256) -> bool:
    self._transfer(msg.sender, _to, amount)
    return True


@external
def transferFrom(_from: address, _to: address, amount: uint256) -> bool:
    # Unlimited approval (saves an SSTORE)
    if (self.allowance[_from][msg.sender] < MAX_UINT256):
        self.allowance[_from][msg.sender] -= amount
        log Approval(_from, msg.sender, self.allowance[_from][msg.sender])
    self._transfer(_from, _to, amount)
    return True


@external
def approve(spender: address, amount: uint256) -> bool:
    self.allowance[msg.sender][spender] = amount
    log Approval(msg.sender, spender, amount)
    return True


@external
def increaseAllowance(spender: address, amount: uint256) -> bool:
    self.allowance[msg.sender][spender] += amount
    log Approval(msg.sender, spender, self.allowance[msg.sender][spender])
    return True


@external
def decreaseAllowance(spender: address, amount: uint256) -> bool:
    self.allowance[msg.sender][spender] -= amount
    log Approval(msg.sender, spender, self.allowance[msg.sender][spender])
    return True


@external
def mint(_to: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"
    assert _to != ZERO_ADDRESS, "to = 0 address"

    # track lastest tx
    self.lastBlock[_to] = block.number

    self.totalSupply += amount
    self.balanceOf[_to] += amount
    log Transfer(ZERO_ADDRESS, _to, amount)


@external
def burn(_from: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"
    assert _from != ZERO_ADDRESS, "from = 0 address"

    # track lastest tx
    self.lastBlock[_from] = block.number

    self.totalSupply -= amount
    self.balanceOf[_from] -= amount
    log Transfer(_from, ZERO_ADDRESS, amount)