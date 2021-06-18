# @version 0.2.12

"""
@title Unagii Vault V2
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

# TODO: comment
# TODO: gas optimize

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


interface Vault:
    def uToken() -> address: view
    def token() -> address: view


interface FundManager:
    def vault() -> address: view
    def token() -> address: view
    # returns loss = debt - total assets in fund manager
    def withdraw(amount: uint256) -> uint256: nonpayable


event SetNextTimeLock:
    nextTimeLock: address


event AcceptTimeLock:
    timeLock: address


event SetGuardian:
    guardian: address


event SetAdmin:
    admin: address


event SetFundManager:
    fundManager: address


event SetPause:
    paused: bool


event SetWhitelist:
    addr: indexed(address)
    approved: bool


event Deposit:
    sender: indexed(address)
    amount: uint256
    diff: uint256
    shares: uint256


event Withdraw:
    owner: indexed(address)
    shares: uint256
    amount: uint256


event Borrow:
    fundManager: indexed(address)
    amount: uint256
    borrowed: uint256


event Repay:
    fundManager: indexed(address)
    amount: uint256
    repaid: uint256


event Report:
    fundManager: indexed(address)
    debt: uint256
    gain: uint256
    loss: uint256
    lockedProfit: uint256


event ForceUpdateBalanceOfVault:
    balanceOfVault: uint256


token: public(ERC20)
uToken: public(UnagiiToken)
fundManager: public(FundManager)
# privileges: time lock >= admin >= guardian
timeLock: public(address)
nextTimeLock: public(address)
guardian: public(address)
admin: public(address)

paused: public(bool)
depositLimit: public(uint256)
# token balance of vault tracked internally to protect against share dilution
# from sending tokens directly to this contract
balanceOfVault: public(uint256)
debt: public(uint256)  # debt to users (amount borrowed by fund manager)
MAX_MIN_RESERVE: constant(uint256) = 10000
minReserve: public(uint256)
lastReport: public(uint256)
lockedProfit: public(uint256)
MAX_DEGRADATION: constant(uint256) = 10 ** 18
lockedProfitDegradation: public(uint256)

blockDelay: public(uint256)
# Token has fee on transfer
feeOnTransfer: public(bool)
whitelist: public(HashMap[address, bool])


@external
def __init__(token: address, uToken: address, guardian: address):
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.guardian = guardian
    self.token = ERC20(token)
    self.uToken = UnagiiToken(uToken)

    assert self.uToken.token() == self.token.address, "uToken.token != token"

    self.paused = True
    self.blockDelay = 1
    self.lastReport = block.timestamp
    self.minReserve = 500 # 5% of free funds
    # 6 hours
    self.lockedProfitDegradation = convert(MAX_DEGRADATION / 21600, uint256)


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


@external
def setNextTimeLock(nextTimeLock: address):
    assert msg.sender == self.timeLock, "!time lock"
    self.nextTimeLock = nextTimeLock
    log SetNextTimeLock(nextTimeLock)


@external
def acceptTimeLock():
    assert msg.sender == self.nextTimeLock, "!next time lock"
    self.timeLock = msg.sender
    log AcceptTimeLock(msg.sender)


@external
def setAdmin(admin: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self.admin = admin
    log SetAdmin(admin)


@external
def setGuardian(guardian: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self.guardian = guardian
    log SetGuardian(guardian)


# TODO: test migration
@external
def setFundManager(fundManager: address):
    assert msg.sender == self.timeLock, "!time lock"

    assert FundManager(fundManager).vault() == self, "fund manager vault != vault"
    assert (
        FundManager(fundManager).token() == self.token.address
    ), "fund manager token != token"

    self.fundManager = FundManager(fundManager)
    log SetFundManager(fundManager)


@external
def setPause(paused: bool):
    assert msg.sender in [self.timeLock, self.admin, self.guardian], "!auth"
    self.paused = paused
    log SetPause(paused)


@external
def setMinReserve(minReserve: uint256):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert minReserve <= MAX_MIN_RESERVE, "min reserve > max"
    self.minReserve = minReserve


@external
def setLockedProfitDegradation(degradation: uint256):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert degradation <= MAX_DEGRADATION, "degradation > max"
    self.lockedProfitDegradation = degradation


@external
def setDepositLimit(limit: uint256):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self.depositLimit = limit


@external
def setBlockDelay(delay: uint256):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert delay >= 1, "delay = 0"
    self.blockDelay = delay


@external
def setFeeOnTransfer(feeOnTransfer: bool):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self.feeOnTransfer = feeOnTransfer


@external
def setWhitelist(addr: address, approved: bool):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
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
    return self.balanceOfVault + self.debt


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

    if lockedFundsRatio < MAX_DEGRADATION:
        lockedProfit: uint256 = self.lockedProfit
        return lockedProfit - lockedFundsRatio * lockedProfit / MAX_DEGRADATION
    else:
        return 0

@external
@view
def calcLockedProfit() -> uint256:
    return self._calcLockedProfit()


@internal
@view
def _calcFreeFunds() -> uint256:
    return self._totalAssets() - self._calcLockedProfit()


@external
@view
def calcFreeFunds() -> uint256:
    return self._calcFreeFunds()


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
    # reverts if free funds = 0
    return amount * totalSupply / freeFunds


@external
@view
def calcSharesToMint(amount: uint256) -> uint256:
    return self._calcSharesToMint(
        amount, self.uToken.totalSupply(), self._calcFreeFunds()
    )


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


@external
@view
def calcWithdraw(shares: uint256) -> uint256:
    return self._calcWithdraw(shares, self.uToken.totalSupply(), self._calcFreeFunds())


@external
@nonreentrant("lock")
def deposit(amount: uint256, _min: uint256) -> uint256:
    assert not self.paused, "paused"
    # TODO: test whitelist
    # TODO: zap / swap
    # TODO: remove?
    assert (
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
        or self.whitelist[msg.sender]
    ), "block < delay"

    _amount: uint256 = min(amount, self.token.balanceOf(msg.sender))
    assert _amount > 0, "deposit = 0"

    assert self._totalAssets() + _amount <= self.depositLimit, "deposit limit"

    totalSupply: uint256 = self.uToken.totalSupply()
    freeFunds: uint256 = self._calcFreeFunds()

    # amount of tokens that this vault received
    diff: uint256 = 0
    if self.feeOnTransfer:
        # Actual amount transferred may be less than `amount`
        # if token has fee on transfer
        diff = self.token.balanceOf(self)
        self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
        diff = self.token.balanceOf(self) - diff
    else:
        self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
        diff = _amount

    assert diff > 0, "diff = 0"

    # calculate with free funds before deposit
    shares: uint256 = self._calcSharesToMint(diff, totalSupply, freeFunds)
    assert shares >= _min, "shares < min"

    self.balanceOfVault += diff
    self.uToken.mint(msg.sender, shares)

    assert self.token.balanceOf(self) >= self.balanceOfVault, "bal < vault"

    log Deposit(msg.sender, _amount, diff, shares)

    return shares


@external
@nonreentrant("lock")
def withdraw(shares: uint256, _min: uint256) -> uint256:
    # TODO: smart contract cannot transferFrom and then withdraw?
    # TODO: zap / swap
    # TODO: test whitelist
    assert (
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
        or self.whitelist[msg.sender]
    ), "block < delay"

    _shares: uint256 = min(shares, self.uToken.balanceOf(msg.sender))
    assert _shares > 0, "shares = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    amount: uint256 = self._calcWithdraw(_shares, totalSupply, self._calcFreeFunds())

    if amount > self.balanceOfVault:
        diff: uint256 = self.token.balanceOf(self)
        # loss must be <= debt
        loss: uint256 = self.fundManager.withdraw(amount - self.balanceOfVault)
        diff = self.token.balanceOf(self) - diff

        if loss > 0:
            # msg.sender must cover all of loss
            amount -= loss
            self.debt -= loss

        self.debt -= diff
        self.balanceOfVault += diff

        if amount > self.balanceOfVault:
            amount = self.balanceOfVault

    self.uToken.burn(msg.sender, _shares)

    assert amount >= _min, "amount < min"
    self.balanceOfVault -= amount

    self._safeTransfer(self.token.address, msg.sender, amount)

    assert self.token.balanceOf(self) >= self.balanceOfVault, "bal < vault"

    log Withdraw(msg.sender, _shares, amount)

    # actual amount received by msg.sender may be less if fee on transfer
    return amount


@internal
@view
def _calcAvailableToInvest() -> uint256:
    if self.paused or self.fundManager.address == ZERO_ADDRESS:
        return 0

    freeFunds: uint256 = self._calcFreeFunds()
    minBal: uint256 = freeFunds * self.minReserve / MAX_MIN_RESERVE

    if self.balanceOfVault > minBal:
        return self.balanceOfVault - minBal
    return 0


@external
@view
def calcAvailableToInvest() -> uint256:
    return self._calcAvailableToInvest()


@external
def borrow(amount: uint256) -> uint256:
    assert not self.paused, "paused"
    assert msg.sender == self.fundManager.address, "!fund manager"

    available: uint256 = self._calcAvailableToInvest()
    _amount: uint256 = min(amount, available)
    assert _amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, _amount)

    self.balanceOfVault -= _amount
    # include fee on trasfer to debt
    self.debt += _amount

    assert self.token.balanceOf(self) >= self.balanceOfVault, "bal < vault"

    log Borrow(msg.sender, amount, _amount)

    return _amount


@external
def repay(amount: uint256) -> uint256:
    assert msg.sender == self.fundManager.address, "!fund manager"

    _amount: uint256 = min(amount, self.debt)
    assert _amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
    diff = self.token.balanceOf(self) - diff

    self.balanceOfVault += diff
    # exclude fee on transfer from debt payment
    self.debt -= diff

    assert self.token.balanceOf(self) >= self.balanceOfVault, "bal < vault"

    log Repay(msg.sender, amount, diff)

    return diff


@external
def report(gain: uint256, loss: uint256):
    assert msg.sender == self.fundManager.address, "!fund manager"
    # can't have both gain and loss > 0
    assert (gain >= 0 and loss == 0) or (gain == 0 and loss >= 0), "gain and loss > 0"

    lockedProfit: uint256 = self._calcLockedProfit()

    if gain > 0:
        assert self.token.balanceOf(msg.sender) >= gain, "gain < bal"

        # free funds = bal + debt + gain - (locked profit + gain)
        self.debt += gain
        self.lockedProfit = lockedProfit + gain
    elif loss > 0:
        # free funds = bal + debt - loss - (locked profit - loss)
        self.debt -= loss
        if lockedProfit > loss:
            self.lockedProfit -= loss
        else:
            # no locked profit to be released
            self.lockedProfit = 0

    self.lastReport = block.timestamp

    # log updated debt and lockedProfit
    log Report(msg.sender, self.debt, gain, loss, self.lockedProfit)


@external
def forceUpdateBalanceOfVault():
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    bal: uint256 = self.token.balanceOf(self)
    assert bal < self.balanceOfVault, "bal >= vault"
    self.balanceOfVault = bal
    log ForceUpdateBalanceOfVault(bal)


@external
def skim():
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self._safeTransfer(
        self.token.address, msg.sender, self.token.balanceOf(self) - self.balanceOfVault
    )


@external
def sweep(token: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, msg.sender, ERC20(token).balanceOf(self))
