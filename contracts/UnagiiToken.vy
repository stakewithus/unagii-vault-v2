# @version 0.2.12

"""
@title Unagii Token
@author stakewith.us
@license AGPL-3.0-or-later
"""
# TODO: comment
# TODO: gas optimize

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


event SetNextTimeLock:
    timeLock: address


event AcceptTimeLock:
    timeLock: address


event SetMinter:
    minter: address


name: public(String[64])
symbol: public(String[32])
# Vyper does not support uint8
decimals: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])
totalSupply: public(uint256)
timeLock: public(address)
nextTimeLock: public(address)
minter: public(address)
token: public(ERC20)
lastBlock: public(HashMap[address, uint256])


@external
def __init__(token: address):
    self.timeLock = msg.sender
    self.token = ERC20(token)
    self.name = concat("unagii_", DetailedERC20(token).name(), "_v2")
    self.symbol = concat("u", DetailedERC20(token).symbol(), "v2")
    self.decimals = DetailedERC20(token).decimals()


@external
def setName(name: String[42]):
    assert msg.sender == self.timeLock, "!time lock"
    self.name = name


@external
def setSymbol(symbol: String[20]):
    assert msg.sender == self.timeLock, "!time lock"
    self.symbol = symbol


@external
def setNextTimeLock(nextTimeLock: address):
    """
    @notice Set next time lock
    @param nextTimeLock Address of next time lock
    """
    assert msg.sender == self.timeLock, "!time lock"
    # allow next time lock = zero address (cancel next time lock)
    self.nextTimeLock = nextTimeLock
    log SetNextTimeLock(nextTimeLock)


@external
def acceptTimeLock():
    """
    @notice Accept time lock
    @dev Only `nextTimeLock` can claim time lock
    """
    assert msg.sender == self.nextTimeLock, "!next time lock"
    self.timeLock = msg.sender
    log AcceptTimeLock(msg.sender)


@external
def setMinter(minter: address):
    """
    @notice Set minter
    @param minter Address of minter
    """
    assert msg.sender == self.timeLock, "!time lock"
    # allow minter = zero address
    self.minter = minter
    log SetMinter(minter)


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
    if self.allowance[_from][msg.sender] < MAX_UINT256:
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


# TODO: permit


@external
def mint(_to: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"
    assert _to not in [self, ZERO_ADDRESS], "invalid receiver"

    # track lastest tx
    self.lastBlock[_to] = block.number

    self.totalSupply += amount
    self.balanceOf[_to] += amount
    log Transfer(ZERO_ADDRESS, _to, amount)


@external
def burn(_from: address, amount: uint256):
    assert msg.sender == self.minter, "!minter"
    assert _from != ZERO_ADDRESS, "from = 0"

    # track lastest tx
    self.lastBlock[_from] = block.number

    self.totalSupply -= amount
    self.balanceOf[_from] -= amount
    log Transfer(_from, ZERO_ADDRESS, amount)
