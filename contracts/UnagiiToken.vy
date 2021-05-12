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
    def decimals() -> uint256: view

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)

minter: public(address)
nextMinter: public(address)
underlying: public(ERC20)

lastBlock: public(HashMap[address, uint256])

@external
def __init__(underlying: address):
    self.minter = msg.sender
    self.underlying = ERC20(underlying)

    # TODO: name
    self.name = concat("unagii_v2_", DetailedERC20(underlying).symbol())
    self.symbol = concat("u2_", DetailedERC20(underlying).symbol())
    self.decimals = DetailedERC20(underlying).decimals()


@external
def setMinter(nextMinter: address):
    """
    @notice Set next minter
    @param nextMinter Address of next minter
    """
    assert msg.sender == self.minter, "!minter"
    # allow next minter = zero address
    self.nextMinter = nextMinter


@external
def acceptMinter():
    """
    @notice Accept minter
    @dev Only `nextMinter` can claim minter 
    """
    assert msg.sender == self.nextMinter, "!next minter"
    self.minter = msg.sender
    self.nextMinter = ZERO_ADDRESS


@internal
def _transfer(sender: address, receiver: address, amount: uint256):
    assert receiver not in [self, ZERO_ADDRESS], "invalid receiver"
    
    # track lastest tx
    self.lastBlock[sender] = block.number
    self.lastBlock[receiver] = block.number

    self.balanceOf[sender] -= amount
    self.balanceOf[receiver] += amount
    log Transfer(sender, receiver, amount)


@external
def mint(receiver: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"

    # track lastest tx
    self.lastBlock[receiver] = block.number

    self.totalSupply += amount
    self.balanceOf[receiver] += amount
    log Transfer(ZERO_ADDRESS, receiver, amount)


@external
def burn(spender: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"

    # track lastest tx
    self.lastBlock[spender] = block.number

    self.totalSupply -= amount
    self.balanceOf[spender] -= amount
    log Transfer(spender, ZERO_ADDRESS, amount)


@external
def transfer(receiver: address, amount: uint256) -> bool:
    self._transfer(msg.sender, receiver, amount)
    return True


@external
def transferFrom(sender: address, receiver: address, amount: uint256) -> bool:
    # Unlimited approval (saves an SSTORE)
    if (self.allowance[sender][msg.sender] < MAX_UINT256):
        self.allowance[sender][msg.sender] -= amount
        log Approval(sender, msg.sender, self.allowance[sender][msg.sender])
    self._transfer(sender, receiver, amount)
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
