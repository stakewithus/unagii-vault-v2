# @version 0.2.12

"""
@title Unagii Vault V2
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

interface DetailedERC20:
    def decimals() -> uint256: view


interface UnagiiToken:
    def token() -> address: view
    def decimals() -> uint256: view
    def totalSupply() -> uint256: view
    def balanceOf(owner: address) -> uint256: view
    def mint(receiver: address, amount: uint256): nonpayable
    def burn(spender: address, amount: uint256): nonpayable
    def lastBlock(owner: address) -> uint256: view


interface IStrategy:
    def vault() -> address: view
    def token() -> address: view
    def totalAssets() -> uint256: view
    def withdraw(amount: uint256) -> uint256: nonpayable


event UpdateAdmin:
    admin: address

event UpdateTimeLock:
    timeLock: address

event UpdateGuardian:
    guardian: address

event UpdateKeeper:
    keeper: address

event SetPause:
    paused: bool

event UpdateDepositLimit:
    depositLimit: uint256

event UpdatePerformanceFee:
    performanceFee: uint256

MAX_BPS: constant(uint256) = 10000
# TODO: remove?
# https://github.com/yearn/yearn-vaults/issues/333
# Adjust for each token PRECISION_FACTOR = 10 ** (18 - token.decimals)
PRECISION_FACTOR: constant(uint256) = 1

token: public(ERC20)
uToken: public(UnagiiToken)
admin: public(address)
nextAdmin: public(address)
timeLock: public(address)
guardian: public(address)
keeper: public(address)

paused: public(bool)

depositLimit: public(uint256)
totalDebtRatio: public(uint256)
totalDebt: public(uint256)
lastReport: public(uint256)
lockedProfit: public(uint256)
DEGRADATION_COEFFICIENT: constant(uint256) = 10 ** 18
lockedProfitDegradation: public(uint256)
balanceInVault: public(uint256)
# TODO: remove?
PERFORMANCE_FEE_CAP: constant(uint256) = 2000
performanceFee: public(uint256)

blockDelay: public(uint256)
# Token has fee on transfer
feeOnTransfer: public(bool)


@external
def __init__(
    token: address,
    uToken: address,
    timeLock: address,
    guardian: address,
    keeper: address
):
    self.admin = msg.sender
    self.timeLock = timeLock
    self.guardian = guardian
    self.keeper = keeper
    self.token = ERC20(token)
    self.uToken = UnagiiToken(uToken)

    assert self.uToken.token() == self.token.address, "uToken.token != token"

    decimals: uint256 = DetailedERC20(self.token.address).decimals()
    if decimals < 18:
        assert PRECISION_FACTOR == 18 - decimals, "precision != 18 - decimals"
    else:
        assert PRECISION_FACTOR == 1, "precision != 1"

    self.paused = True
    self.blockDelay = 10


@external
def setNextAdmin(_nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    assert _nextAdmin != self.admin, "next admin = current"
    self.nextAdmin = _nextAdmin


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    log UpdateAdmin(msg.sender)


@external 
def setTimeLock(timeLock: address):
    assert msg.sender == self.admin, "!admin"
    self.timeLock = timeLock
    log UpdateTimeLock(timeLock)


@external 
def setGuardian(guardian: address):
    assert msg.sender == self.admin, "!admin"
    self.guardian = guardian
    log UpdateGuardian(guardian)


@external 
def setKeeper(keeper: address):
    assert msg.sender == self.admin, "!admin"
    self.keeper = keeper
    log UpdateKeeper(keeper)


@external
def setPause(paused: bool):
    assert msg.sender in [self.admin, self.guardian], "!authorized"
    self.paused = paused
    log SetPause(paused)


@external
def setLockedProfitDegradation(degradation: uint256):
    assert msg.sender == self.admin, "!admin"
    assert degradation <= DEGRADATION_COEFFICIENT
    self.lockedProfitDegradation = degradation


@external
def setDepositLimit(limit: uint256):
    assert msg.sender == self.admin
    self.depositLimit = limit
    log UpdateDepositLimit(limit)


@external
def setPerformanceFee(fee: uint256):
    assert msg.sender == self.admin, "!admin"
    assert fee <= PERFORMANCE_FEE_CAP
    self.performanceFee = fee
    log UpdatePerformanceFee(fee)


@external
def setBlockDelay(delay: uint256):
    assert msg.sender == self.admin, "!admin"
    assert delay >= 1, "delay = 0"
    self.blockDelay = delay


@external
def setFeeOnTransfer(feeOnTransfer: bool):
    assert msg.sender == self.admin, "!admin"
    self.feeOnTransfer = feeOnTransfer


@internal
def _safeTransfer(token: address, receiver: address, amount: uint256):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("transfer(address,uint256)"),
            convert(receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(res) > 0:
        assert convert(res, bool), "transfer failed"


@internal
def _safeTransferFrom(token: address, sender: address, receiver: address, amount: uint256):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(sender, bytes32),
            convert(receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(res) > 0:
        assert convert(res, bool), "transferFrom failed"


@internal
@view
def _totalAssets() -> uint256:
    return self.balanceInVault + self.totalDebt


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


@internal
@pure
def _calcSharesToMint(amount: uint256, totalSupply: uint256, totalAssets: uint256) -> uint256:
    # mint
    # s = shares to mint
    # T = total shares before mint
    # a = deposit amount
    # P = total amount of underlying token in vault + strategy before deposit
    # s / (T + s) = a / (P + a)
    # sP = aT
    # a = 0               | mint s = 0
    # a > 0, T = 0, P = 0 | mint s = a
    # a > 0, T > 0, P = 0 | invalid state (a = 0) 
    # a > 0, T = 0, P > 0 | s = 0, but mint s = a as if P = 0
    # a > 0, T > 0, P > 0 | mint s = a / P * T
    if amount == 0:
        return 0
    if totalSupply == 0:
        return amount
    # reverts if total assets = 0
    # TODO: PRECISION_FACTOR
    return amount * totalSupply / totalAssets 


@internal
@pure
def _calcSharesToBurn(amount: uint256, totalSupply: uint256, totalAssets: uint256) -> uint256:
    # burn
    # s = shares to burn
    # T = total shares before burn
    # a = withdraw amount
    # P = total amount of underlying token in vault + strategy before deposit
    # s / (T - s) = a / (P - a), (constraints T >= s, P >= a)
    # sP = aT
    # a = 0               | burn s = 0
    # a > 0, T = 0, P = 0 | invalid state (a > P = 0)
    # a > 0, T > 0, P = 0 | invalid state (a > P = 0)
    # a > 0, T = 0, P > 0 | burn s = 0 (T = 0 >= s) TODO: secure?
    # a > 0, T > 0, P > 0 | burn s = a / P * T
    if amount == 0:
        return 0
    # reverts if total assets = 0
    # TODO: PRECISION_FACTOR
    return amount * totalSupply / totalAssets


@view
@internal
def _calcLockedProfit() -> uint256:
    # TODO: math
    lockedFundsRatio: uint256 = (block.timestamp - self.lastReport) * self.lockedProfitDegradation

    if(lockedFundsRatio < DEGRADATION_COEFFICIENT):
        lockedProfit: uint256 = self.lockedProfit
        return lockedProfit - (
                lockedFundsRatio
                * lockedProfit
                / DEGRADATION_COEFFICIENT
            )
    else:        
        return 0


@internal
@pure
def _calcWithdraw(shares: uint256, totalSupply: uint256, totalAssets: uint256) -> uint256:
    # s = shares
    # T = total supply of shares
    # a = amount to withdraw
    # P = total amount of underlying token in vault + strategy
    # s / T = a / P (constraints T >= s, P >= a)
    # sP = aT
    # s = 0 | a = 0
    # s > 0, T = 0, P = 0 | invalid state (s > T = 0)
    # s > 0, T > 0, P = 0 | a = 0
    # s > 0, T = 0, P > 0 | invalid state (s > T = 0)
    # s > 0, T > 0, P > 0 | a = s / T * P

    # # TODO: PRECISION_FACTOR
    # # return PRECISION_FACTOR * shares * freeFunds / totalSupply / PRECISION_FACTOR
    # return shares * freeFunds / totalSupply
    if shares == 0:
        return 0
    # invalid if total supply = 0
    return shares * totalAssets / totalSupply


@external
@view
def calcWithdraw(shares: uint256) -> uint256:
    totalSupply: uint256 = self.uToken.totalSupply()
    totalAssets: uint256 = self._totalAssets()
    freeFunds: uint256 = totalAssets - self._calcLockedProfit()
    return self._calcWithdraw(shares, totalSupply, freeFunds)


# TODO: deposit log
@external
@nonreentrant("lock")
def deposit(amount: uint256, minShares: uint256) -> uint256:
    assert not self.paused, "paused"
    assert block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay, "block < delay" 

    _amount: uint256 = amount
    if _amount == MAX_UINT256:
        _amount = self.token.balanceOf(msg.sender)
    assert _amount > 0, "deposit = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    totalAssets: uint256 = self._totalAssets()

    diff: uint256 = 0
    if self.feeOnTransfer:
        # Actual amount transferred may be less than `_amount`,
        # for example if token has fee on transfer
        diff = self.token.balanceOf(self)
        self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
        diff = self.token.balanceOf(self) - diff
    else:
        self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
        diff = _amount

    assert diff > 0, "diff = 0"

    shares: uint256 = self._calcSharesToMint(diff, totalSupply, totalAssets)
    assert shares >= minShares, "shares < min"
    
    self.balanceInVault += diff
    self.uToken.mint(msg.sender, shares)

    return shares


# TODO: withdraw log
@external
@nonreentrant("withdraw")
def withdraw(shares: uint256, minAmount: uint256) -> uint256:
    # TODO: smart contract cannot transferFrom and then withdraw
    assert block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay, "block < delay" 

    _shares: uint256 = min(shares, self.uToken.balanceOf(msg.sender))
    assert _shares > 0, "shares = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    totalAssets: uint256 = self._totalAssets()
    freeFunds: uint256 = totalAssets - self._calcLockedProfit()
    amount: uint256 = self._calcWithdraw(_shares, totalSupply, freeFunds)

    totalLoss: uint256 = 0
    if amount > self.balanceInVault:
        # TODO:
        pass

    self.uToken.burn(msg.sender, _shares)

    diff: uint256 = 0
    if self.feeOnTransfer:
        diff = self.token.balanceOf(self)
        self._safeTransfer(self.token.address, msg.sender, amount)
        diff  = self.token.balanceOf(self) - diff
    else:
        self._safeTransfer(self.token.address, msg.sender, amount)
        diff = amount

    assert diff >= minAmount, "diff < min"
    self.balanceInVault -= diff

    # TODO: remove?
    # assert bal >= self.balanceInVault, "bal < balance in vault"

    return diff


# @external
# def borrow(amount: uint256):
#     assert self.strategies[msg.sender].active, "!active"

#     available: uint256 = self._creditAvailable(msg.sender)
#     _amount: uint256 = min(amount, available)
#     assert _amount > 0, "borrow = 0"

#     self._safeTransfer(self.token.address, msg.sender, _amount)

#     # include fee on trasfer to debt 
#     self.strategies[msg.sender].debt += amount
#     self.totalDebt += amount
#     self.balanceInVault -= amount

#     # TODO: remove?
#     # bal: uint256 = self.token.balanceOf(self)
#     # assert bal >= self.balanceInVault(self), "bal < balance in vault"


# @external
# def repay(amount: uint256):
#     assert self.strategies[msg.sender].active, "!active"
#     assert amount > 0, "repay = 0"

#     diff: uint256 = self.token.balanceOf(self)
#     self._safeTransferFrom(self.token.address, msg.sender, self, amount)
#     diff  = self.token.balanceOf(self) - diff

#     self.strategies[msg.sender].debt -= diff
#     self.totalDebt -= diff
#     self.balanceInVault += diff

    # TODO: remove?
    # bal: uint256 = self.token.balanceOf(self)
    # assert bal >= self.balanceInVault(self), "bal < balance in vault"


# # migration

# # u = token token
# # ut = unagi token
# # v1 = vault 1
# # v2 = vault 2

# # v2.pause
# # v1.pause
# # ut.setMinter(v2)
# # u.approve(v2, bal of v1, {from: v1})
# # u.transferFrom(v1, v2, bal of v1, {from: v2})

@external
def skim():
    assert msg.sender == self.admin, "!admin"
    diff: uint256 = self.token.balanceOf(self) - self.balanceInVault
    self._safeTransfer(self.token.address, self.admin, diff)


@external
def sweep(token: address):
    assert msg.sender == self.admin, "!admin"
    assert token != self.token.address, "protected token"
    self._safeTransfer(token, self.admin, ERC20(token).balanceOf(self))