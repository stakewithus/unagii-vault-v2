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


MAX_STRATEGIES: constant(uint256) = 20

struct Strategy:
    approved: bool
    active: bool
    debtRatio: uint256
    debt: uint256
    gain: uint256
    loss: uint256
    minDebtPerHarvest: uint256
    maxDebtPerHarvest: uint256

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

event ApproveStrategy:
    strategy: indexed(address)

event RevokeStrategy:
    strategy: indexed(address)

event AddStrategyToQueue:
    strategy: indexed(address)

event RemoveStrategyFromQueue:
    strategy: indexed(address)

event UpdateWithdrawalQueue:
    queue: address[MAX_STRATEGIES]

event SetWhitelist:
    addr: indexed(address)
    approved: bool


token: public(ERC20)
uToken: public(UnagiiToken)
admin: public(address)
nextAdmin: public(address)
timeLock: public(address)
guardian: public(address)
keeper: public(address)

strategies: public(HashMap[address, Strategy])
withdrawalQueue: public(address[MAX_STRATEGIES])

paused: public(bool)

# TODO: remove?
depositLimit: public(uint256)
totalDebtRatio: public(uint256)
totalDebt: public(uint256)
lastReport: public(uint256)
lockedProfit: public(uint256)
DEGRADATION_COEFFICIENT: constant(uint256) = 10 ** 18
lockedProfitDegradation: public(uint256)
balanceInVault: public(uint256)
MAX_BPS: constant(uint256) = 10000
# TODO: remove?
PERFORMANCE_FEE_CAP: constant(uint256) = 2000
performanceFee: public(uint256)

# TODO: remove?
# https://github.com/yearn/yearn-vaults/issues/333
# Adjust for each token PRECISION_FACTOR = 10 ** (18 - token.decimals)
PRECISION_FACTOR: constant(uint256) = 1

blockDelay: public(uint256)
# Token has fee on transfer
feeOnTransfer: public(bool)
whitelist: public(HashMap[address, bool])


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
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    assert nextAdmin != self.admin, "next admin = current"
    self.nextAdmin = nextAdmin


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
    assert (
        self.whitelist[msg.sender] or
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay" 

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
    # TODO: smart contract cannot transferFrom and then withdraw?
    assert (
        self.whitelist[msg.sender] or
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay" 

    _shares: uint256 = min(shares, self.uToken.balanceOf(msg.sender))
    assert _shares > 0, "shares = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    totalAssets: uint256 = self._totalAssets()
    freeFunds: uint256 = totalAssets - self._calcLockedProfit()
    amount: uint256 = self._calcWithdraw(_shares, totalSupply, freeFunds)

    totalLoss: uint256 = 0
    if amount > self.balanceInVault:
        for strategy in self.withdrawalQueue:
            if strategy == ZERO_ADDRESS:
                break

            if amount <= self.balanceInVault:
                break

            debt: uint256 = self.strategies[strategy].debt
            amountNeeded: uint256 = min(amount - self.balanceInVault, debt)
            if amountNeeded == 0:
                continue
            
            loss: uint256 = 0
            totalAssetsBefore: uint256 = IStrategy(strategy).totalAssets()
            if debt > totalAssetsBefore:
                loss = debt - totalAssetsBefore

            diff: uint256 = self.token.balanceOf(self)
            IStrategy(strategy).withdraw(amountNeeded)
            diff = self.token.balanceOf(self) - diff

            totalAssetsAfter: uint256 = IStrategy(strategy).totalAssets()
            if totalAssetsBefore - totalAssetsAfter > diff:
                loss += totalAssetsBefore - totalAssetsAfter - diff

            # NOTE: Withdrawer incurs any losses from liquidation
            if loss > 0:
                amount -= loss
                totalLoss += loss
                # TODO:
                # self._reportLoss(strategy, loss)
                self.strategies[strategy].debt -= loss
                self.totalDebt -= loss

            # Reduce the Strategy's debt by the amount withdrawn ("realized returns")
            # NOTE: This doesn't add to returns as it's not earned by "normal means"
            # TODO: underflow?
            self.strategies[strategy].debt -= diff
            self.totalDebt -= diff
            self.balanceInVault += diff

        if amount > self.balanceInVault:
            amount = self.balanceInVault
            # NOTE: Burn # of shares that corresponds to what Vault has on-hand,
            #       including the losses that were incurred above during withdrawal
            totalAssets = self._totalAssets()
            _shares = self._calcSharesToBurn(amount + totalLoss, totalSupply, totalAssets)

    # NOTE: This loss protection is put in place to revert if losses from
    #       withdrawing are more than what is considered acceptable.
    # assert totalLoss <= PRECISION_FACTOR * maxLoss * (amount + totalLoss) / MAX_BPS / PREPRECISION_FACTOR

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
# def approveStrategy(strategy: address):
#     assert not self.paused, "paused"
#     assert msg.sender == self.timeLock, "!time lock"

#     assert not self.strategies[strategy].approved, "approved"
#     assert IStrategy(strategy).vault() == self, "strategy.vault != vault"
#     assert IStrategy(strategy).token() == self.token.address, "strategy.token != token"

#     self.strategies[strategy] = Strategy({
#         approved: True,
#         debt: 0
#     })
#     log ApproveStrategy(strategy)


# @external
# def revokeStrategy(strategy: address):
#     assert msg.sender == self.admin, "!admin"
#     assert self.strategies[strategy].approved, "!approved"
#     assert strategy not in self.withdrawalQueue, "active"

#     self.strategies[strategy].approved = False
#     log RevokeStrategy(strategy)


# @internal
# def _pack():
#     arr: address[MAX_STRATEGIES] = empty(address[MAX_STRATEGIES])
#     i: uint256 = 0
#     for strat in self.withdrawalQueue:
#         if strat != ZERO_ADDRESS:
#             arr[i] = strat
#             i += 1
#     self.withdrawalQueue = arr


# @internal
# def _append(strategy: address):
#     assert self.withdrawalQueue[MAX_STRATEGIES - 1] == ZERO_ADDRESS, "active > max"
#     self.withdrawalQueue[MAX_STRATEGIES - 1] = strategy
#     self._pack()


# @internal
# def _remove(i: uint256):
#     assert i < MAX_STRATEGIES, "i >= max"
#     self.withdrawalQueue[i] = ZERO_ADDRESS
#     self._pack()


# @internal
# @view
# def _find(strategy: address) -> uint256:
#     for i in range(MAX_STRATEGIES):
#         if self.withdrawalQueue[i] == strategy:
#             return i
#     raise "strategy not found"


# @external
# def addStrategyToQueue(strategy: address):
#     assert msg.sender == self.admin, "!admin"
#     assert self.strategies[strategy].approved, "!approved"
#     assert strategy not in self.withdrawalQueue, "active"

#     self._append(strategy)
#     log AddStrategyToQueue(strategy)


# @external
# def removeStrategyFromQueue(strategy: address):
#     assert msg.sender == self.admin, "!admin"
#     assert strategy in self.withdrawalQueue, "!active"

#     i: uint256 = self._find(strategy)
#     self._remove(i)
#     log RemoveStrategyFromQueue(strategy)

@external
def setWithdrawalQueue(queue: address[MAX_STRATEGIES]):
    assert msg.sender == self.admin, "!admin"

    # Check old and new queue lengths of non zero strategies are equal
    zeroFound: bool = False
    for i in range(MAX_STRATEGIES):
        oldStrat: address = self.withdrawalQueue[i]
        newStrat: address = queue[i]

        if oldStrat != ZERO_ADDRESS:
            # Check no gaps
            assert not zeroFound, "zero address found"
            assert newStrat != ZERO_ADDRESS, "new strat == 0 address"
        else:
            if not zeroFound:
                zeroFound = True
            assert newStrat == ZERO_ADDRESS, "new strat != 0 address"

    # Check strategy is active and no duplicate
    for i in range(MAX_STRATEGIES):
        strat: address = queue[i]
        if strat == ZERO_ADDRESS:
            break
        assert self.strategies[strat].active, "!active"
        self.strategies[strat].active = False

    for i in range(MAX_STRATEGIES):
        strat: address = queue[i]
        if strat == ZERO_ADDRESS:
            break
        self.strategies[strat].active = True
        self.withdrawalQueue[i] = strat

    log UpdateWithdrawalQueue(queue)


@view
@internal
def _creditAvailable(strategy: address) -> uint256:
    if self.paused:
        return 0

    totalAssets: uint256 = self._totalAssets()
    totalDebtLimit: uint256 =  self.totalDebtRatio * totalAssets / MAX_BPS 
    totalDebt: uint256 = self.totalDebt
    debtLimit: uint256 = self.strategies[strategy].debtRatio * totalAssets / MAX_BPS
    debt: uint256 = self.strategies[strategy].debt
    minDebtPerHarvest: uint256 = self.strategies[strategy].minDebtPerHarvest
    maxDebtPerHarvest: uint256 = self.strategies[strategy].maxDebtPerHarvest

    if totalDebt >= totalDebtLimit or debt >= debtLimit:
        return 0

    available: uint256 = min(debtLimit - debt, totalDebtLimit - totalDebt)
    # TODO: use self.balanceInVault?
    available = min(available, self.token.balanceOf(self))

    # TODO: what?
    # Adjust by min and max borrow limits (per harvest)
    # NOTE: min increase can be used to ensure that if a strategy has a minimum
    #       amount of capital needed to purchase a position, it's not given capital
    #       it can't make use of yet.
    # NOTE: max increase is used to make sure each harvest isn't bigger than what
    #       is authorized. This combined with adjusting min and max periods in
    #       `BaseStrategy` can be used to effect a "rate limit" on capital increase.
    if available < minDebtPerHarvest:
        return 0
    else:
        return min(available, maxDebtPerHarvest)


@external
@view
def creditAvailable(strategy: address) -> uint256:
    return self._creditAvailable(strategy)


@external
def borrow(amount: uint256):
    assert self.strategies[msg.sender].active, "!active"

    available: uint256 = self._creditAvailable(msg.sender)
    _amount: uint256 = min(amount, available)
    assert _amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, _amount)

    # include fee on trasfer to debt 
    self.strategies[msg.sender].debt += amount
    self.totalDebt += amount
    self.balanceInVault -= amount

    # TODO: remove?
    # bal: uint256 = self.token.balanceOf(self)
    # assert bal >= self.balanceInVault(self), "bal < balance in vault"


@external
def repay(amount: uint256):
    assert self.strategies[msg.sender].active, "!active"
    assert amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, amount)
    diff  = self.token.balanceOf(self) - diff

    self.strategies[msg.sender].debt -= diff
    self.totalDebt -= diff
    self.balanceInVault += diff

    # TODO: remove?
    # bal: uint256 = self.token.balanceOf(self)
    # assert bal >= self.balanceInVault(self), "bal < balance in vault"


@view
@internal
def _debtOutstanding(strategy: address) -> uint256:
    debt: uint256 = self.strategies[strategy].debt
    if self.totalDebtRatio == 0:
        return debt

    debtLimit: uint256 = self.strategies[strategy].debtRatio * self.totalDebt / self.totalDebtRatio

    if self.paused:
        return debt
    elif debt <= debtLimit:
        return 0
    else:
        return debt - debtLimit


@view
@internal
def _calculateLockedProfit() -> uint256:
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


@external
def report(gain: uint256, loss: uint256, _debtPayment: uint256) -> uint256:
    assert self.strategies[msg.sender].active, "!active"
    assert self.token.balanceOf(msg.sender) >= gain + _debtPayment

    # We have a loss to report, do it before the rest of the calculations
    if loss > 0:
        # TODO: report loss
        # self._reportLoss(msg.sender, loss)
        pass

    # Assess both management fee and performance fee, and issue both as shares of the vault
    totalFees: uint256 = gain * self.performanceFee / MAX_BPS

    # Returns are always "realized gains"
    self.strategies[msg.sender].gain += gain

    # Compute the line of credit the Vault is able to offer the Strategy (if any)
    credit: uint256 = self._creditAvailable(msg.sender)

    # Outstanding debt the Strategy wants to take back from the Vault (if any)
    # NOTE: debtOutstanding <= StrategyParams.totalDebt
    debt: uint256 = self._debtOutstanding(msg.sender)
    debtPayment: uint256 = min(_debtPayment, debt)

    if debtPayment > 0:
        self.strategies[msg.sender].debt -= debtPayment
        self.totalDebt -= debtPayment
        debt -= debtPayment
        # NOTE: `debt` is being tracked for later

    # Update the actual debt based on the full credit we are extending to the Strategy
    # or the returns if we are taking funds back
    # NOTE: credit + self.strategies[msg.sender].totalDebt is always < self.debtLimit
    # NOTE: At least one of `credit` or `debt` is always 0 (both can be 0)
    if credit > 0:
        self.strategies[msg.sender].debt += credit
        self.totalDebt += credit

    # Give/take balance to Strategy, based on the difference between the reported gains
    # (if any), the debt payment (if any), the credit increase we are offering (if any),
    # and the debt needed to be paid off (if any)
    # NOTE: This is just used to adjust the balance of tokens between the Strategy and
    #       the Vault based on the Strategy's debt limit (as well as the Vault's).
    totalAvail: uint256 = gain + debtPayment
    if totalAvail < credit:  # credit surplus, give to Strategy
        self._safeTransfer(self.token.address, msg.sender, credit - totalAvail)
    elif totalAvail > credit:  # credit deficit, take from Strategy
        self._safeTransferFrom(self.token.address, msg.sender, self, totalAvail - credit)
    # else, don't do anything because it is balanced

    # Profit is locked and gradually released per block
    # NOTE: compute current locked profit and replace with sum of current and new
    lockedProfitBeforeLoss :uint256 = self._calculateLockedProfit() + gain - totalFees 
    if lockedProfitBeforeLoss > loss: 
        self.lockedProfit = lockedProfitBeforeLoss - loss
    else:
       self.lockedProfit = 0 


    # Update reporting time
    # TODO: self.strategies[msg.sender].lastReport = block.timestamp
    self.lastReport = block.timestamp

    # log StrategyReported(
    #     msg.sender,
    #     gain,
    #     loss,
    #     debtPayment,
    #     self.strategies[msg.sender].totalGain,
    #     self.strategies[msg.sender].totalLoss,
    #     self.strategies[msg.sender].totalDebt,
    #     credit,
    #     self.strategies[msg.sender].debtRatio,
    # )

    if self.strategies[msg.sender].debtRatio == 0 or self.paused:
        # Take every last penny the Strategy has (Emergency Exit/revokeStrategy)
        # NOTE: This is different than `debt` in order to extract *all* of the returns
        return IStrategy(msg.sender).totalAssets()
    else:
        # Otherwise, just return what we have as debt outstanding
        return debt


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