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
    def migrate(newVersion: address): nonpayable


MAX_STRATEGIES: constant(uint256) = 20
MAX_BPS: constant(uint256) = 10000
MAX_PERFORMANCE_FEE: constant(uint256) = 5000

struct Strategy:
    approved: bool
    active: bool
    activated: bool
    debtRatio: uint256
    debt: uint256
    totalGain: uint256
    totalLoss: uint256
    performanceFee: uint256
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

event SetWhitelist:
    addr: indexed(address)
    approved: bool

event UpdateDepositLimit:
    depositLimit: uint256

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

event StrategyUpdateDebtRatio:
    strategy: indexed(address)
    debtRatio: uint256

event StrategyUpdateMinDebtPerHarvest:
    strategy: indexed(address)
    minDebtPerHarvest: uint256

event StrategyUpdateMaxDebtPerHarvest:
    strategy: indexed(address)
    maxDebtPerHarvest: uint256

event StrategyUpdatePerformanceFee:
    strategy: indexed(address)
    performanceFee: uint256

event Report:
    strategy: indexed(address)
    gain: uint256
    loss: uint256
    debtPaid: uint256
    totalGain: uint256
    totalLoss: uint256
    debt: uint256
    debtAdded: uint256
    debtRatio: uint256

event Borrow:
    strategy: indexed(address)
    amount: uint256

event Repay:
    strategy: indexed(address)
    amount: uint256

event MigrateStrategy:
    oldVersion: indexed(address)
    newVersion: indexed(address)


token: public(ERC20)
uToken: public(UnagiiToken)
admin: public(address)
nextAdmin: public(address)
timeLock: public(address)
guardian: public(address)
keeper: public(address)

paused: public(bool)
depositLimit: public(uint256)
totalDebt: public(uint256)
totalDebtRatio: public(uint256)
balanceInVault: public(uint256)
lastReport: public(uint256)
lockedProfit: public(uint256)
DEGRADATION_COEFFICIENT: constant(uint256) = 10 ** 18
lockedProfitDegradation: public(uint256)

strategies: public(HashMap[address, Strategy])
withdrawalQueue: public(address[MAX_STRATEGIES])

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

    self.paused = True
    self.blockDelay = 10
    self.lastReport = block.timestamp
    # 6 hours
    self.lockedProfitDegradation = convert(DEGRADATION_COEFFICIENT / 21600 , uint256)


@external
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    assert nextAdmin != self.admin, "next admin = current"
    self.nextAdmin = nextAdmin


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    self.nextAdmin = ZERO_ADDRESS
    log UpdateAdmin(msg.sender)


@external 
def setTimeLock(timeLock: address):
    assert msg.sender == self.timeLock, "!time lock"
    assert timeLock != self.timeLock, "new time lock = current"
    self.timeLock = timeLock
    log UpdateTimeLock(timeLock)


@external 
def setGuardian(guardian: address):
    assert msg.sender == self.admin, "!admin"
    assert guardian != self.guardian, "new guardian = current"
    self.guardian = guardian
    log UpdateGuardian(guardian)


@external 
def setKeeper(keeper: address):
    assert msg.sender == self.admin, "!admin"
    assert keeper != self.keeper, "new keeper = current"
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
    assert degradation <= DEGRADATION_COEFFICIENT, "degradation > max"
    self.lockedProfitDegradation = degradation


@external
def setDepositLimit(limit: uint256):
    assert msg.sender == self.admin, "!admin"
    self.depositLimit = limit
    log UpdateDepositLimit(limit)


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
def _safeTransferFrom(token: address, owner: address, receiver: address, amount: uint256):
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
    return self.balanceInVault + self.totalDebt


@external
@view
def totalAssets() -> uint256:
    return self._totalAssets()


@internal
@view
def _calcLockedProfit() -> uint256:
    lockedFundsRatio: uint256 = (block.timestamp - self.lastReport) * self.lockedProfitDegradation

    if(lockedFundsRatio < DEGRADATION_COEFFICIENT):
        lockedProfit: uint256 = self.lockedProfit
        return lockedProfit - lockedFundsRatio * lockedProfit / DEGRADATION_COEFFICIENT
    else:        
        return 0


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
def _calcSharesToMint(amount: uint256, totalSupply: uint256, freeFunds: uint256) -> uint256:
    # s = shares to mint
    # T = total shares before mint
    # a = deposit amount
    # P = total amount of underlying token in vault + strategy before deposit
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


@internal
@pure
def _calcSharesToBurn(amount: uint256, totalSupply: uint256, freeFunds: uint256) -> uint256:
    # s = shares to burn
    # T = total shares before burn
    # a = withdraw amount
    # P = total amount of underlying token in vault + strategy
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


@internal
@pure
def _calcWithdraw(shares: uint256, totalSupply: uint256, freeFunds: uint256) -> uint256:
    # s = shares
    # T = total supply of shares
    # a = amount to withdraw
    # P = total amount of underlying token in vault + strategy
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


# TODO: deposit log
# TODO: deposit limit
# TODO: test deposit / withdraw flash attack
@external
@nonreentrant("lock")
def deposit(_amount: uint256, minShares: uint256) -> uint256:
    assert not self.paused, "paused"
    assert (
        self.whitelist[msg.sender] or
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay" 

    amount: uint256 = _amount
    if amount == MAX_UINT256:
        amount = self.token.balanceOf(msg.sender)

    assert self._totalAssets() + amount <= self.depositLimit, "deposit limit"
    assert amount > 0, "deposit = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
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

    return shares


@internal
def _reportLoss(strategy: address, loss: uint256):
    debt: uint256 = self.strategies[strategy].debt
    assert loss <= debt, "loss > debt"

    dr: uint256 = 0 # change in debt ratio
    if self.totalDebtRatio != 0:
        # l = loss
        # D = total debt
        # x = ratio of loss
        # R = total debt ratio
        # l / D = x / R
        dr = min(
            loss * self.totalDebtRatio / self.totalDebt,
            self.strategies[strategy].debtRatio,
        )
    self.strategies[strategy].totalLoss += loss
    self.strategies[strategy].debt -= loss
    self.totalDebt -= loss
    self.strategies[strategy].debtRatio -= dr
    self.totalDebtRatio -= dr


@internal
def _withdrawFromStrategies(_amount: uint256) -> uint256:
    amount: uint256 = _amount
    totalLoss: uint256 = 0
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
        totalAssetsDiff: uint256 = totalAssetsBefore - totalAssetsAfter
        if totalAssetsDiff > diff:
            loss += totalAssetsDiff - diff

        if loss > 0:
            amount -= loss
            totalLoss += loss
            self._reportLoss(strategy, loss)

        self.strategies[strategy].debt -= diff
        self.totalDebt -= diff
        self.balanceInVault += diff

    return totalLoss


# TODO: withdraw log
@external
@nonreentrant("lock")
def withdraw(_shares: uint256, minAmount: uint256) -> uint256:
    # TODO: smart contract cannot transferFrom and then withdraw?
    assert (
        self.whitelist[msg.sender] or
        block.number >= self.uToken.lastBlock(msg.sender) + self.blockDelay
    ), "block < delay" 

    shares: uint256 = min(_shares, self.uToken.balanceOf(msg.sender))
    assert shares > 0, "shares = 0"

    totalSupply: uint256 = self.uToken.totalSupply()
    freeFunds: uint256 = self._calcFreeFunds()
    amount: uint256 = self._calcWithdraw(shares, totalSupply, freeFunds)

    if amount > self.balanceInVault:
        totalLoss: uint256 = self._withdrawFromStrategies(amount)
        amount -= totalLoss
        if amount > self.balanceInVault:
            amount = self.balanceInVault
            shares = self._calcSharesToBurn(amount + totalLoss, totalSupply, self._totalAssets())

    self.uToken.burn(msg.sender, shares)

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


@internal
def _pack():
    arr: address[MAX_STRATEGIES] = empty(address[MAX_STRATEGIES])
    i: uint256 = 0
    for strat in self.withdrawalQueue:
        if strat != ZERO_ADDRESS:
            arr[i] = strat
            i += 1
    self.withdrawalQueue = arr


@internal
def _append(strategy: address):
    assert self.withdrawalQueue[MAX_STRATEGIES - 1] == ZERO_ADDRESS, "active > max"
    self.withdrawalQueue[MAX_STRATEGIES - 1] = strategy
    self._pack()


@internal
def _remove(i: uint256):
    assert i < MAX_STRATEGIES, "i >= max"
    self.withdrawalQueue[i] = ZERO_ADDRESS
    self._pack()


@internal
@view
def _find(strategy: address) -> uint256:
    for i in range(MAX_STRATEGIES):
        if self.withdrawalQueue[i] == strategy:
            return i
    raise "strategy not found"


@external
def approveStrategy(
    strategy: address,
    minDebtPerHarvest: uint256,
    maxDebtPerHarvest: uint256,
    performanceFee: uint256
):
    assert not self.paused, "paused"
    assert msg.sender == self.timeLock, "!time lock"

    assert not self.strategies[strategy].approved, "approved"
    assert IStrategy(strategy).vault() == self, "strategy.vault != vault"
    assert IStrategy(strategy).token() == self.token.address, "strategy.token != token"

    assert minDebtPerHarvest <= maxDebtPerHarvest, "min > max"
    assert performanceFee <= MAX_PERFORMANCE_FEE, "performance fee > max"

    self.strategies[strategy] = Strategy({
        approved: True,
        active: False,
        activated: False,
        debtRatio: 0,
        debt: 0,
        totalGain: 0,
        totalLoss: 0,
        minDebtPerHarvest: minDebtPerHarvest,
        maxDebtPerHarvest: maxDebtPerHarvest,
        performanceFee: performanceFee
    })
    log ApproveStrategy(strategy)


@external
def revokeStrategy(strategy: address):
    assert msg.sender in [self.admin, self.guardian], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"

    self.strategies[strategy].approved = False
    log RevokeStrategy(strategy)


@external
def addStrategyToQueue(strategy: address, debtRatio: uint256):
    assert not self.paused, "paused"
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"
    assert self.totalDebtRatio + debtRatio <= MAX_BPS, "total debt ratio > max"

    self._append(strategy)
    self.strategies[strategy].active = True
    self.strategies[strategy].activated = True
    self.strategies[strategy].debtRatio = debtRatio
    self.totalDebtRatio += debtRatio
    log AddStrategyToQueue(strategy)


@external
def removeStrategyFromQueue(strategy: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].active, "!active"

    self._remove(self._find(strategy))
    self.strategies[strategy].active = False
    self.totalDebtRatio -= self.strategies[strategy].debtRatio
    self.strategies[strategy].debtRatio = 0
    log RemoveStrategyFromQueue(strategy)


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


@external
def updateStrategyDebtRatio(strategy: address, debtRatio: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].active, "!active"
    self.totalDebtRatio -= self.strategies[strategy].debtRatio
    self.strategies[strategy].debtRatio = debtRatio
    self.totalDebtRatio += debtRatio
    assert self.totalDebtRatio <= MAX_BPS, "total debt ratio > max"
    log StrategyUpdateDebtRatio(strategy, debtRatio)


@external
def updateStrategyMinDebtPerHarvest(strategy: address, minDebtPerHarvest: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert self.strategies[strategy].maxDebtPerHarvest >= minDebtPerHarvest
    self.strategies[strategy].minDebtPerHarvest = minDebtPerHarvest
    log StrategyUpdateMinDebtPerHarvest(strategy, minDebtPerHarvest)


@external
def updateStrategyMaxDebtPerHarvest(strategy: address, maxDebtPerHarvest: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert self.strategies[strategy].minDebtPerHarvest <= maxDebtPerHarvest
    self.strategies[strategy].maxDebtPerHarvest = maxDebtPerHarvest
    log StrategyUpdateMaxDebtPerHarvest(strategy, maxDebtPerHarvest)


@external
def updateStrategyPerformanceFee(strategy: address, performanceFee: uint256):
    assert msg.sender == self.admin, "!admin"
    assert performanceFee <= MAX_PERFORMANCE_FEE, "performance fee > max"
    assert self.strategies[strategy].approved, "!approved"
    self.strategies[strategy].performanceFee = performanceFee
    log StrategyUpdatePerformanceFee(strategy, performanceFee)


# TODO: migrate strategy

@internal
@view
def _calcOutstandingDebt(strategy: address) -> uint256:
    if self.totalDebtRatio == 0:
        return self.strategies[strategy].debt

    limit: uint256 = self.strategies[strategy].debtRatio * self.totalDebt / self.totalDebtRatio
    debt: uint256 = self.strategies[strategy].debt

    if self.paused:
        return debt
    elif debt <= limit:
        return 0
    else:
        return debt - limit


@external
@view
def calcOutstandingDebt(strategy: address) -> uint256:
    return self._calcOutstandingDebt(strategy)


@internal
@view
def _calcAvailableCredit(strategy: address) -> uint256:
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
    #TODO: use token.balanceOf(self)?
    available = min(available, self.balanceInVault)

    if available < minDebtPerHarvest:
        return 0
    else:
        return min(available, maxDebtPerHarvest)


@external
@view
def calcAvailableCredit(strategy: address) -> uint256:
    return self._calcAvailableCredit(strategy)


@external
def report(gain: uint256, loss: uint256, _debtPayment: uint256) -> uint256:
    assert self.strategies[msg.sender].active, "!active"
    assert self.token.balanceOf(msg.sender) >= gain + _debtPayment

    if loss > 0:
        self._reportLoss(msg.sender, loss)

    fee: uint256 = gain * self.strategies[msg.sender].performanceFee / MAX_BPS

    # TODO: include fee on transfer
    self.strategies[msg.sender].totalGain += gain

    credit: uint256 = self._calcAvailableCredit(msg.sender)

    debt: uint256 = self._calcOutstandingDebt(msg.sender)
    debtPayment: uint256 = min(_debtPayment, debt)

    if debtPayment > 0:
        self.strategies[msg.sender].debt -= debtPayment
        self.totalDebt -= debtPayment
        debt -= debtPayment

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
    lockedProfitBeforeLoss :uint256 = self._calcLockedProfit() + gain - fee 
    if lockedProfitBeforeLoss > loss: 
        self.lockedProfit = lockedProfitBeforeLoss - loss
    else:
       self.lockedProfit = 0 

    # Update reporting time
    self.lastReport = block.timestamp

    log Report(
        msg.sender,
        gain,
        loss,
        debtPayment,
        self.strategies[msg.sender].totalGain,
        self.strategies[msg.sender].totalLoss,
        self.strategies[msg.sender].debt,
        credit,
        self.strategies[msg.sender].debtRatio,
    )

    if self.strategies[msg.sender].debtRatio == 0 or self.paused:
        # Take every last penny the Strategy has (Emergency Exit/revokeStrategy)
        # NOTE: This is different than `debt` in order to extract *all* of the returns
        return IStrategy(msg.sender).totalAssets()
    else:
        # Otherwise, just return what we have as debt outstanding
        return debt


@external
def borrow(_amount: uint256) -> uint256:
    assert not self.paused, "paused"
    assert self.strategies[msg.sender].active, "!active"

    available: uint256 = self._calcAvailableCredit(msg.sender)
    amount: uint256 = min(_amount, available)
    assert amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, amount)

    # include fee on trasfer to debt 
    self.strategies[msg.sender].debt += amount
    self.totalDebt += amount
    self.balanceInVault -= amount

    # TODO: remove?
    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < balance in vault"

    log Borrow(msg.sender, amount)

    return amount


@external
def repay(amount: uint256) -> uint256:
    assert self.strategies[msg.sender].active, "!active"
    assert amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, amount)
    diff  = self.token.balanceOf(self) - diff

    # exclude fee on transfer from debt payment
    self.strategies[msg.sender].debt -= diff
    self.totalDebt -= diff
    self.balanceInVault += diff

    # TODO: remove?
    assert self.token.balanceOf(self) >= self.balanceInVault, "bal < balance in vault"

    log Repay(msg.sender, diff)

    return diff


@external
def migrateStrategy(oldVersion: address, newVersion: address):
    assert msg.sender == self.admin, "!admin"
    assert self.strategies[oldVersion].active, "old !active"
    assert self.strategies[newVersion].approved, "new !approved"
    assert not self.strategies[newVersion].activated, "activated"

    strategy: Strategy = self.strategies[oldVersion]

    self.strategies[newVersion] = Strategy({
        approved: True,
        active: True,
        activated: True,
        performanceFee: strategy.performanceFee,
        debtRatio: strategy.debtRatio,
        minDebtPerHarvest: strategy.minDebtPerHarvest,
        maxDebtPerHarvest: strategy.maxDebtPerHarvest,
        debt: strategy.debt,
        totalGain: 0,
        totalLoss: 0,
    })

    self.strategies[oldVersion].active = False
    self.strategies[oldVersion].debtRatio = 0
    self.strategies[oldVersion].debt = 0
    log RevokeStrategy(oldVersion)

    i: uint256 = self._find(oldVersion)
    self.withdrawalQueue[i] = newVersion

    IStrategy(oldVersion).migrate(newVersion)
    log MigrateStrategy(oldVersion, newVersion)


# TODO: migrate vault

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