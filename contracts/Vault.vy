# @version 0.2.12

"""
@title Unagii Vault V2
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

# TODO: comment


interface DetailedERC20:
    def decimals() -> uint256: view


interface UnagiiToken:
    def setNextMinter(minter: address): nonpayable
    def acceptMinter(): nonpayable
    def token() -> address: view
    def decimals() -> uint256: view
    def totalSupply() -> uint256: view
    def balanceOf(owner: address) -> uint256: view
    def mint(receiver: address, amount: uint256): nonpayable
    def burn(spender: address, amount: uint256): nonpayable
    def lastBlock(owner: address) -> uint256: view


interface Vault:
    def uToken() -> address: view
    def token() -> address: view


interface FundManager:
    def vault() -> address: view
    def token() -> address: view
    def totalAssets() -> uint256: view
    def withdraw(amount: uint256) -> uint256: nonpayable


MAX_MIN_RESERVE: constant(uint256) = 10000


event SetNextAdmin:
    nextAdmin: address


event AcceptAdmin:
    admin: address


event SetNextTimeLock:
    nextTimeLock: address


event AcceptTimeLock:
    timeLock: address


event SetGuardian:
    guardian: address


event SetFundManager:
    fundManager: address


event SetPause:
    paused: bool


event SetWhitelist:
    addr: indexed(address)
    approved: bool


event Borrow:
    fundManager: indexed(address)
    amount: uint256


event Repay:
    fundManager: indexed(address)
    amount: uint256


event ForceUpdateBalanceInVault:
    balanceInVault: uint256


token: public(ERC20)
uToken: public(UnagiiToken)
fundManager: public(FundManager)
admin: public(address)
nextAdmin: public(address)
timeLock: public(address)
nextTimeLock: public(address)
guardian: public(address)

paused: public(bool)
depositLimit: public(uint256)
balanceInVault: public(uint256)
debt: public(uint256)  # debt to users (amount borrowed by fund manager)
minReserve: public(uint256)
lastReport: public(uint256)
lockedProfit: public(uint256)
DEGRADATION_COEFFICIENT: constant(uint256) = 10 ** 18
lockedProfitDegradation: public(uint256)

blockDelay: public(uint256)
# Token has fee on transfer
feeOnTransfer: public(bool)
whitelist: public(HashMap[address, bool])

# TODO: test events
@external
def __init__(
    token: address,
    uToken: address,
    guardian: address,
):
    self.admin = msg.sender
    self.timeLock = msg.sender
    self.guardian = guardian
    self.token = ERC20(token)
    self.uToken = UnagiiToken(uToken)

    assert self.uToken.token() == self.token.address, "uToken.token != token"

    self.paused = True
    self.blockDelay = 1
    self.lastReport = block.timestamp
    self.minReserve = 500
    # 6 hours
    self.lockedProfitDegradation = convert(DEGRADATION_COEFFICIENT / 21600, uint256)


# TODO: migrate to new vault

# u = token token
# ut = unagi token
# v1 = vault 1
# v2 = vault 2

# v2.pause
# v1.pause
# ut.setMinter(v2)
# u.approve(v2, bal of v1, {from: v1})
# u.transferFrom(v1, v2, bal of v1, {from: v2})
# update balance in vault and debt?

# @external
# def setNextMinter(vault: address):
#     # TODO: pause?
#     assert msg.sender == self.timeLock, "!time lock"
#     assert vault != self, "new vault = current"

#     # vault = ZERO_ADDRESS means cancel next minter
#     if vault != ZERO_ADDRESS:
#         assert Vault(vault).token() == self.token.address, "vault token != token"
#         assert Vault(vault).uToken() == self.uToken.address, "vault uToken != uToken"

#     # this will fail if self != minter
#     self.uToken.setNextMinter(vault)

# TODO: test
@external
def acceptMinter():
    assert msg.sender == self.admin, "!admin"
    # this will fail if self != minter
    self.uToken.acceptMinter()


@external
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    assert nextAdmin != self.admin, "next admin = current"
    self.nextAdmin = nextAdmin
    log SetNextAdmin(nextAdmin)


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    log AcceptAdmin(msg.sender)


@external
def setNextTimeLock(nextTimeLock: address):
    assert msg.sender == self.timeLock, "!time lock"
    assert nextTimeLock != self.timeLock, "next time lock = current"
    self.nextTimeLock = nextTimeLock
    log SetNextTimeLock(nextTimeLock)


@external
def acceptTimeLock():
    assert msg.sender == self.nextTimeLock, "!next time lock"
    self.timeLock = msg.sender
    log AcceptTimeLock(msg.sender)


@external
def setGuardian(guardian: address):
    assert msg.sender == self.admin, "!admin"
    assert guardian != self.guardian, "new guardian = current"
    self.guardian = guardian
    log SetGuardian(guardian)


# TODO: test migration
@external
def setFundManager(fundManager: address):
    assert msg.sender == self.timeLock, "!time lock"
    assert fundManager != self.fundManager.address, "new fund manager = current"

    assert FundManager(fundManager).vault() == self, "fund manager vault != vault"
    assert (
        FundManager(fundManager).token() == self.token.address
    ), "fund manager token != token"

    self.fundManager = FundManager(fundManager)
    log SetFundManager(fundManager)


@external
def setPause(paused: bool):
    assert msg.sender in [self.admin, self.guardian], "!auth"
    self.paused = paused
    log SetPause(paused)


@external
def setMinReserve(minReserve: uint256):
    assert msg.sender == self.admin, "!admin"
    assert minReserve <= MAX_MIN_RESERVE, "min reserve > max"
    self.minReserve = minReserve


@external
def setLockedProfitDegradation(degradation: uint256):
    assert msg.sender == self.admin, "!admin"
    assert degradation <= DEGRADATION_COEFFICIENT, "degradation > max"
    self.lockedProfitDegradation = degradation


@external
def setDepositLimit(limit: uint256):
    assert msg.sender == self.admin, "!admin"
    self.depositLimit = limit


@external
def setBlockDelay(delay: uint256):
    assert msg.sender == self.admin, "!admin"
    assert delay >= 1, "delay = 0"
    self.blockDelay = delay


@external
def setFeeOnTransfer(feeOnTransfer: bool):
    assert msg.sender == self.admin, "!admin"
    self.feeOnTransfer = feeOnTransfer


@external
def setWhitelist(addr: address, approved: bool):
    assert msg.sender == self.admin, "!admin"
    self.whitelist[addr] = approved
    log SetWhitelist(addr, approved)


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
def _safeTransferFrom(
    token: address, owner: address, receiver: address, amount: uint256
):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(owner, bytes32),
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
    return self.balanceInVault + self.debt


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


@internal
@view
def _calcLockedProfit() -> uint256:
    lockedFundsRatio: uint256 = (
        block.timestamp - self.lastReport
    ) * self.lockedProfitDegradation

    if lockedFundsRatio < DEGRADATION_COEFFICIENT:
        lockedProfit: uint256 = self.lockedProfit
        return lockedProfit - lockedFundsRatio * lockedProfit / DEGRADATION_COEFFICIENT
    else:
        return 0


@internal
@view
def _calcFreeFunds() -> uint256:
    return self._totalAssets() - self._calcLockedProfit()


# TODO: test
@external
@view
def calcFreeFunds() -> uint256:
    return self._calcFreeFunds()


# TODO: test
@internal
@pure
def _calcSharesToMint(
    amount: uint256, totalSupply: uint256, freeFunds: uint256
) -> uint256:
    # s = shares to mint
    # T = total shares before mint
    # a = deposit amount
    # P = total amount of underlying token in vault + fund manager before deposit
    # s / (T + s) = a / (P + a)
    # sP = aT
    # a = 0               | mint s = 0
    # a > 0, T = 0, P = 0 | mint s = a
    # a > 0, T = 0, P > 0 | mint s = a as if P = 0
    # a > 0, T > 0, P = 0 | invalid, equation cannot be true for any s
    # a > 0, T > 0, P > 0 | mint s = aT / P
    if amount == 0:
        return 0
    if totalSupply == 0:
        return amount
    # reverts if total assets = 0
    return amount * totalSupply / freeFunds


# TODO: test
@internal
@pure
def _calcSharesToBurn(
    amount: uint256, totalSupply: uint256, freeFunds: uint256
) -> uint256:
    # s = shares to burn
    # T = total shares before burn
    # a = withdraw amount
    # P = total amount of underlying token in vault + fund manager
    # s / (T - s) = a / (P - a), (constraints T >= s, P >= a)
    # sP = aT
    # a = 0               | burn s = 0
    # a > 0, T = 0, P = 0 | invalid (violates constraint P >= a)
    # a > 0, T = 0, P > 0 | burn s = 0
    # a > 0, T > 0, P = 0 | invalid (violates constraint P >= a)
    # a > 0, T > 0, P > 0 | burn s = aT / P
    if amount == 0:
        return 0
    # reverts if total assets = 0
    return amount * totalSupply / freeFunds


# TODO: test
@internal
@pure
def _calcWithdraw(shares: uint256, totalSupply: uint256, freeFunds: uint256) -> uint256:
    # s = shares
    # T = total supply of shares
    # a = amount to withdraw
    # P = total amount of underlying token in vault + fund manager
    # s / T = a / P (constraints T >= s, P >= a)
    # sP = aT
    # s = 0               | a = 0
    # s > 0, T = 0, P = 0 | invalid (violates constraint T >= s)
    # s > 0, T = 0, P > 0 | invalid (violates constraint T >= s)
    # s > 0, T > 0, P = 0 | a = 0
    # s > 0, T > 0, P > 0 | a = sP / T
    if shares == 0:
        return 0
    # invalid if total supply = 0
    return shares * freeFunds / totalSupply


# TODO: test
@external
@view
def calcWithdraw(shares: uint256) -> uint256:
    return self._calcWithdraw(shares, self.uToken.totalSupply(), self._calcFreeFunds())


# TODO: deposit log
@external
@nonreentrant("lock")
def deposit(_amount: uint256, minShares: uint256) -> uint256:
    assert not self.paused, "paused"
    # TODO: test deposit / withdraw flash attack
    # TODO: test block delay
    # TODO: test whitelist
    assert (
        self.whitelist[msg.sender]
        or block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay"

    amount: uint256 = _amount
    if amount == MAX_UINT256:
        amount = self.token.balanceOf(msg.sender)

    assert self._totalAssets() + amount <= self.depositLimit, "deposit limit"
    assert amount > 0, "deposit = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    # TODO: test free funds
    freeFunds: uint256 = self._calcFreeFunds()

    diff: uint256 = 0
    if self.feeOnTransfer:
        # Actual amount transferred may be less than `amount`,
        # for example if token has fee on transfer
        diff = self.token.balanceOf(self)
        self._safeTransferFrom(self.token.address, msg.sender, self, amount)
        diff = self.token.balanceOf(self) - diff
    else:
        self._safeTransferFrom(self.token.address, msg.sender, self, amount)
        diff = amount

    assert diff > 0, "diff = 0"

    shares: uint256 = self._calcSharesToMint(diff, totalSupply, freeFunds)
    assert shares >= minShares, "shares < min"

    # TODO: test balanceInVault <= ERC20.balanceOf(self)
    self.balanceInVault += diff
    self.uToken.mint(msg.sender, shares)

    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < vault"

    return shares


# TODO: withdraw log
@external
@nonreentrant("lock")
def withdraw(_maxShares: uint256, _min: uint256) -> uint256:
    # TODO: smart contract cannot transferFrom and then withdraw?
    # TODO: test flash deposit / withdraw
    # TODO: test whitelist
    assert (
        self.whitelist[msg.sender]
        or block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay"

    shares: uint256 = min(_maxShares, self.uToken.balanceOf(msg.sender))
    assert shares > 0, "shares = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    amount: uint256 = self._calcWithdraw(shares, totalSupply, self._calcFreeFunds())

    if amount > self.balanceInVault:
        diff: uint256 = self.token.balanceOf(self)
        loss: uint256 = self.fundManager.withdraw(amount - self.balanceInVault)
        diff = self.token.balanceOf(self) - diff

        if loss > 0:
            amount -= loss
            self.debt -= loss

        self.debt -= diff
        self.balanceInVault += diff

        if amount > self.balanceInVault:
            amount = self.balanceInVault
            shares = self._calcSharesToBurn(
                amount + loss, totalSupply, self._calcFreeFunds()
            )

    self.uToken.burn(msg.sender, shares)

    diff: uint256 = 0
    if self.feeOnTransfer:
        diff = self.token.balanceOf(self)
        self._safeTransfer(self.token.address, msg.sender, amount)
        diff = self.token.balanceOf(self) - diff
    else:
        self._safeTransfer(self.token.address, msg.sender, amount)
        diff = amount

    assert diff >= _min, "diff < min"
    self.balanceInVault -= diff

    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < vault"

    return diff


@internal
@view
def _calcAvailableToInvest() -> uint256:
    if self.paused:
        return 0

    if self.fundManager.address == ZERO_ADDRESS:
        return 0

    freeFunds: uint256 = self._calcFreeFunds()
    minReserve: uint256 = freeFunds * self.minReserve / MAX_MIN_RESERVE

    if self.balanceInVault > minReserve:
        return self.balanceInVault - minReserve
    return 0


# TODO: test
@external
def calcAvailableToInvest() -> uint256:
    return self._calcAvailableToInvest()


@internal
@view
def _calcOutstandingDebt() -> uint256:
    if self.paused:
        return self.debt

    freeFunds: uint256 = self._calcFreeFunds()

    limit: uint256 = (MAX_MIN_RESERVE - self.minReserve) * freeFunds / MAX_MIN_RESERVE
    debt: uint256 = self.debt

    if debt >= limit:
        return debt - limit
    return 0


# TODO: test? remove?
@external
def calcOutstandingDebt() -> uint256:
    return self._calcOutstandingDebt()


# TODO: test
@external
def borrow(_amount: uint256) -> uint256:
    assert not self.paused, "paused"
    assert msg.sender == self.fundManager.address, "!fund manager"

    available: uint256 = self._calcAvailableToInvest()
    amount: uint256 = min(_amount, available)
    assert amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, amount)

    self.balanceInVault -= amount
    # include fee on trasfer to debt
    self.debt += amount

    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < vault"

    log Borrow(msg.sender, amount)

    return amount


# TODO: test
@external
def repay(amount: uint256) -> uint256:
    assert msg.sender == self.fundManager.address, "!fund manager"
    assert amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, amount)
    diff = self.token.balanceOf(self) - diff

    self.balanceInVault += diff
    # exclude fee on transfer from debt payment
    self.debt -= diff

    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < vault"

    log Repay(msg.sender, diff)

    return diff


@external
def report():
    assert msg.sender == self.fundManager.address, "!fund manager"
    total: uint256 = self.fundManager.totalAssets()
    debt: uint256 = self.debt
    gain: uint256 = 0
    loss: uint256 = 0
    lockedProfit: uint256 = self._calcLockedProfit()

    if total > debt:
        gain = total - debt
    else:
        loss = debt - total

    if gain > 0:
        free: uint256 = self.token.balanceOf(msg.sender)
        gain = min(gain, free)

        self.debt += gain
        self.lockedProfit = lockedProfit + gain
    elif loss > 0:
        if lockedProfit > loss:
            self.lockedProfit -= loss
        else:
            self.lockedProfit = 0
            self.debt -= loss - lockedProfit

    self.lastReport = block.timestamp


@external
def forceUpdateBalanceInVault():
    assert msg.sender == self.admin, "!admin"
    bal: uint256 = self.token.balanceOf(self)
    assert bal < self.balanceInVault, "bal >= vault"
    self.balanceInVault = bal
    log ForceUpdateBalanceInVault(bal)


@external
def skim():
    assert msg.sender == self.admin, "!admin"
    diff: uint256 = self.token.balanceOf(self) - self.balanceInVault
    self._safeTransfer(self.token.address, self.admin, diff)


@external
def sweep(token: address):
    assert msg.sender == self.admin, "!admin"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, self.admin, ERC20(token).balanceOf(self))
