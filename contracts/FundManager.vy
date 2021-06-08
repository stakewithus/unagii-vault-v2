# @version 0.2.12

"""
@title Unagii FundManager
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20


interface Vault:
    def token() -> address: view
    def debt() -> uint256: view
    def borrow(amount: uint256) -> uint256: nonpayable
    def repay(amount: uint256) -> uint256: nonpayable
    def report(gain: uint256, loss: uint256): nonpayable


interface IStrategy:
    def fundManager() -> address: view
    def token() -> address: view
    def totalAssets() -> uint256: view
    def deposit(amount: uint256): nonpayable
    def withdraw(amount: uint256) -> uint256: nonpayable
    # TODO: migrate
    def migrate(newVersion: address): nonpayable


MAX_QUEUE: constant(uint256) = 20
MAX_BPS: constant(uint256) = 10000
MAX_PERF_FEE: constant(uint256) = 5000


struct Strategy:
    approved: bool
    active: bool
    activatedAt: uint256
    debtRatio: uint256
    debt: uint256
    # TODO: remove?
    totalGain: uint256
    # TODO: remove?
    totalLoss: uint256
    # TODO: remove
    perfFee: uint256
    # TODO: remove?
    minDebtPerHarvest: uint256
    # TODO: remove?
    maxDebtPerHarvest: uint256


event SetNextAdmin:
    nextAdmin: address


event AcceptAdmin:
    admin: address


event SetGuardian:
    guardian: address


event SetKeeper:
    keeper: address


event SetWorker:
    worker: address

event SetPause:
    paused: bool

event SetVault:
    vault: address

event ApproveStrategy:
    strategy: indexed(address)

event RevokeStrategy:
    strategy: indexed(address)

event AddStrategyToQueue:
    strategy: indexed(address)

event RemoveStrategyFromQueue:
    strategy: indexed(address)

event SetQueue:
    queue: address[MAX_QUEUE]

event UpdateStrategyDebtRatio:
    strategy: indexed(address)
    debtRatio: uint256

event UpdateStrategyMinDebtPerHarvest:
    strategy: indexed(address)
    minDebtPerHarvest: uint256

event UpdateStrategyMaxDebtPerHarvest:
    strategy: indexed(address)
    maxDebtPerHarvest: uint256

event UpdateStrategyPerformanceFee:
    strategy: indexed(address)
    perfFee: uint256

event BorrowFromVault:
    vault: indexed(address)
    amount: uint256
    borrowed: uint256

event RepayVault:
    vault: indexed(address)
    amount: uint256
    repaid: uint256

event ReportToVault:
    vault: indexed(address)
    total: uint256
    debt: uint256
    gain: uint256
    loss: uint256

event Borrow:
    strategy: indexed(address)
    amount: uint256

event Repay:
    strategy: indexed(address)
    amount: uint256

event Report:
    strategy: indexed(address)
    gain: uint256
    loss: uint256
    debt: uint256

vault: public(Vault)
token: public(ERC20)
# privileges - admin > keeper > guardian, worker
admin: public(address)
nextAdmin: public(address)
guardian: public(address) # TODO: remove?
keeper: public(address)
worker: public(address)

paused: public(bool)
totalDebt: public(uint256)
totalDebtRatio: public(uint256)
strategies: public(HashMap[address, Strategy])
queue: public(address[MAX_QUEUE])


@external
def __init__(
    token: address,
    guardian: address,
    keeper: address,
    worker: address
):
    self.token = ERC20(token)
    self.admin = msg.sender
    self.guardian = guardian
    self.keeper = keeper
    self.worker = worker

# TODO: migrate

@external
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    self.nextAdmin = nextAdmin
    log SetNextAdmin(nextAdmin)


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    log AcceptAdmin(msg.sender)


@external
def setGuardian(guardian: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    self.guardian = guardian
    log SetGuardian(guardian)


@external
def setKeeper(keeper: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    self.keeper = keeper
    log SetKeeper(keeper)


@external
def setWorker(worker: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    self.worker = worker
    log SetWorker(worker)


@external
def setPause(paused: bool):
    assert msg.sender in [self.admin, self.keeper, self.guardian], "!auth"
    self.paused = paused
    log SetPause(paused)


# TODO: test migration
@external
def setVault(vault: address):
    assert msg.sender == self.admin, "!admin"
    assert Vault(vault).token() == self.token.address, "vault token != token"
    self.vault = Vault(vault)
    self.token.approve(vault, MAX_UINT256)
    log SetVault(vault)


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
    return self.token.balanceOf(self) + self.totalDebt


@external
def totalAssets() -> uint256:
    return self._totalAssets()

# array functions tested in test/Array.vy 
@internal
def _pack():
    arr: address[MAX_QUEUE] = empty(address[MAX_QUEUE])
    i: uint256 = 0
    for strat in self.queue:
        if strat != ZERO_ADDRESS:
            arr[i] = strat
            i += 1
    self.queue = arr


@internal
def _append(strategy: address):
    assert self.queue[MAX_QUEUE - 1] == ZERO_ADDRESS, "queue > max"
    self.queue[MAX_QUEUE - 1] = strategy
    self._pack()


@internal
def _remove(i: uint256):
    assert i < MAX_QUEUE, "i >= max"
    assert self.queue[i] != ZERO_ADDRESS, "!zero address"
    self.queue[i] = ZERO_ADDRESS
    self._pack()


@internal
@view
def _find(strategy: address) -> uint256:
    for i in range(MAX_QUEUE):
        if self.queue[i] == strategy:
            return i
    raise "not found"


@external
def approveStrategy(
    strategy: address,
    minDebtPerHarvest: uint256,
    maxDebtPerHarvest: uint256,
    perfFee: uint256
):
    assert msg.sender == self.admin, "!admin"

    assert not self.strategies[strategy].approved, "approved"
    assert IStrategy(strategy).fundManager() == self, "strategy fund manager != this"
    assert IStrategy(strategy).token() == self.token.address, "strategy token != token"

    assert minDebtPerHarvest <= maxDebtPerHarvest, "min > max"
    assert perfFee <= MAX_PERF_FEE, "perf fee > max"

    self.strategies[strategy] = Strategy({
        approved: True,
        active: False,
        activatedAt: 0,
        debtRatio: 0,
        debt: 0,
        totalGain: 0,
        totalLoss: 0,
        minDebtPerHarvest: minDebtPerHarvest,
        maxDebtPerHarvest: maxDebtPerHarvest,
        perfFee: perfFee
    })
    log ApproveStrategy(strategy)


@external
def revokeStrategy(strategy: address):
    # TODO: remove guardian?
    assert msg.sender in [self.admin, self.keeper, self.guardian], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"

    # TODO: if strategy.totalDebt > 0?
    self.strategies[strategy].approved = False
    log RevokeStrategy(strategy)


@external
def addStrategyToQueue(strategy: address, debtRatio: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"
    # assert self.totalDebtRatio + debtRatio <= MAX_BPS, "ratio > max"

    self._append(strategy)
    self.strategies[strategy].active = True
    self.strategies[strategy].activatedAt = block.timestamp
    self.strategies[strategy].debtRatio = debtRatio
    # self.totalDebtRatio += debtRatio
    log AddStrategyToQueue(strategy)


@external
def removeStrategyFromQueue(strategy: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].active, "!active"

    self._remove(self._find(strategy))
    self.strategies[strategy].active = False
    # self.totalDebtRatio -= self.strategies[strategy].debtRatio
    self.strategies[strategy].debtRatio = 0
    log RemoveStrategyFromQueue(strategy)


@external
def setQueue(queue: address[MAX_QUEUE]):
    assert msg.sender in [self.admin, self.keeper], "!auth"

    # check no gaps in new queue
    zero: bool = False
    for i in range(MAX_QUEUE):
        strat: address = queue[i]
        if strat == ZERO_ADDRESS:
            if not zero:
                zero = True
        else:
            assert not zero, "gap"

    # Check old and new queue counts of non zero strategies are equal
    for i in range(MAX_QUEUE):
        oldStrat: address = self.queue[i]
        newStrat: address = queue[i]
        if oldStrat == ZERO_ADDRESS:
            assert newStrat == ZERO_ADDRESS, "new != 0"
        else:
            assert newStrat != ZERO_ADDRESS, "new = 0"

    # Check new strategy is active and no duplicate
    for i in range(MAX_QUEUE):
        strat: address = queue[i]
        if strat == ZERO_ADDRESS:
            break
        # code below will fail if duplicate strategy in new queue
        assert self.strategies[strat].active, "!active"
        self.strategies[strat].active = False

    # update queue
    for i in range(MAX_QUEUE):
        strat: address = queue[i]
        if strat == ZERO_ADDRESS:
            break
        self.strategies[strat].active = True
        self.queue[i] = strat

    log SetQueue(queue)


@external
def updateStrategyDebtRatio(strategy: address, debtRatio: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].active, "!active"
    # self.totalDebtRatio -= self.strategies[strategy].debtRatio
    self.strategies[strategy].debtRatio = debtRatio
    # self.totalDebtRatio += debtRatio
    # assert self.totalDebtRatio <= MAX_BPS, "total > max"
    log UpdateStrategyDebtRatio(strategy, debtRatio)


@external
def updateStrategyMinDebtPerHarvest(strategy: address, minDebtPerHarvest: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert self.strategies[strategy].maxDebtPerHarvest >= minDebtPerHarvest, "min > max"
    self.strategies[strategy].minDebtPerHarvest = minDebtPerHarvest
    log UpdateStrategyMinDebtPerHarvest(strategy, minDebtPerHarvest)


@external
def updateStrategyMaxDebtPerHarvest(strategy: address, maxDebtPerHarvest: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert self.strategies[strategy].minDebtPerHarvest <= maxDebtPerHarvest, "max < min"
    self.strategies[strategy].maxDebtPerHarvest = maxDebtPerHarvest
    log UpdateStrategyMaxDebtPerHarvest(strategy, maxDebtPerHarvest)


# TODO: update debt ratios

@external
def updateStrategyPerformanceFee(strategy: address, perfFee: uint256):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert perfFee <= MAX_PERF_FEE, "perf fee > max"
    self.strategies[strategy].perfFee = perfFee
    log UpdateStrategyPerformanceFee(strategy, perfFee)


@internal
def _reportLoss(strategy: address, loss: uint256):
    debt: uint256 = self.strategies[strategy].debt
    assert loss <= debt, "loss > debt"

    dr: uint256 = 0 # change in debt ratio
    # if self.totalDebtRatio != 0:
    #     # l = loss
    #     # D = total debt
    #     # x = ratio of loss
    #     # R = total debt ratio
    #     # l / D = x / R
    #     dr = min(
    #         loss * self.totalDebtRatio / self.totalDebt,
    #         self.strategies[strategy].debtRatio,
    #     )
    self.strategies[strategy].totalLoss += loss
    self.strategies[strategy].debt -= loss
    self.totalDebt -= loss
    self.strategies[strategy].debtRatio -= dr
    # self.totalDebtRatio -= dr


@internal
def _withdrawFromStrategies(_amount: uint256) -> uint256:
    amount: uint256 = _amount
    totalLoss: uint256 = 0
    for strategy in self.queue:
        if strategy == ZERO_ADDRESS:
            break

        bal: uint256 = self.token.balanceOf(self)
        if amount <= bal:
            break

        debt: uint256 = self.strategies[strategy].debt
        amountNeeded: uint256 = min(amount - bal, debt)
        if amountNeeded == 0:
            continue

        diff: uint256 = self.token.balanceOf(self)
        loss: uint256 = IStrategy(strategy).withdraw(amountNeeded)
        diff = self.token.balanceOf(self) - diff

        if loss > 0:
            amount -= loss
            totalLoss += loss
            self._reportLoss(strategy, loss)

        self.strategies[strategy].debt -= diff
        # self.totalDebt -= diff

    return totalLoss


# functions between Vault and this contract
@external
def withdraw(_amount: uint256) -> uint256:
    assert msg.sender == self.vault.address, "!vault"
    
    amount: uint256 = _amount
    bal: uint256 = self.token.balanceOf(self)
    loss: uint256 = 0
    if amount > bal:
        loss = self._withdrawFromStrategies(amount - bal)
        amount -= loss
    
    self._safeTransfer(self.token.address, msg.sender, min(amount, self.token.balanceOf(self)))

    return loss


@external
def borrowFromVault(amount: uint256):
    # TODO: re-order array to save gas?
    assert msg.sender in [self.admin, self.keeper, self.worker], "!auth"
    borrowed: uint256 = self.vault.borrow(amount)
    log BorrowFromVault(self.vault.address, amount, borrowed)


@external
def repayVault(amount: uint256):
    # TODO: re-order array to save gas?
    assert msg.sender in [self.admin, self.keeper, self.worker], "!auth"
    # infinite approved in setVault()
    repaid: uint256 = self.vault.repay(amount)
    log RepayVault(self.vault.address, amount, repaid)


@external
def reportToVault():
    assert msg.sender in [self.admin, self.keeper, self.worker], "!auth"

    total: uint256 = self._totalAssets()
    debt: uint256 = self.vault.debt()
    gain: uint256 = 0
    loss: uint256 = 0

    if total > debt:
        # TODO: if bal part of debt?
        gain = min(total - debt, self.token.balanceOf(self))
    else:
        loss = debt - total
    
    log ReportToVault(self.vault.address, total, debt, gain, loss)

    self.vault.report(gain, loss)


# functions between this contract and strategies
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

# TODO: test
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
    limit: uint256 = self.strategies[strategy].debtRatio * totalAssets / MAX_BPS
    debt: uint256 = self.strategies[strategy].debt

    if debt >= limit:
        return 0

    available: uint256 = min(limit - debt, self.token.balanceOf(self))

    if available < self.strategies[strategy].minDebtPerHarvest:
        return 0
    else:
        return min(available, self.strategies[strategy].maxDebtPerHarvest)


# TODO: test
@external
@view
def calcAvailableCredit(strategy: address) -> uint256:
    return self._calcAvailableCredit(strategy)

@external
def borrow(_amount: uint256):
    assert not self.paused, "paused"
    assert self.strategies[msg.sender].active, "!active"

    available: uint256 = self._calcAvailableCredit(msg.sender)
    amount: uint256 = min(_amount, available)
    assert amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, amount)

    self.strategies[msg.sender].debt += amount
    self.totalDebt += amount

    log Borrow(msg.sender, amount)


@external
def repay(_amount: uint256):
    assert self.strategies[msg.sender].approved, "!approved"

    debt: uint256 = self._calcOutstandingDebt(msg.sender)
    amount: uint256 = min(_amount, debt)
    assert amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, amount)
    diff = self.token.balanceOf(self) - diff

    # exclude fee on transfer from debt payment
    self.strategies[msg.sender].debt -= diff
    self.totalDebt -= diff

    log Repay(msg.sender, diff)


@external
def report(gain: uint256, loss: uint256):
    assert self.strategies[msg.sender].active, "!active"
    # can't have both gain and loss > 0
    assert (gain >= 0 and loss == 0) or (gain == 0 and loss >= 0), "gain and loss > 0"
    assert self.token.balanceOf(msg.sender) >= gain, "bal < gain"

    if gain > 0:
        # TODO: check total assets ?
        # TODO: diff?
        self._safeTransferFrom(self.token.address, msg.sender, self, gain)
    elif loss > 0:
        self._reportLoss(msg.sender, loss)
    
    log Report(msg.sender, gain, loss, self.strategies[msg.sender].debt)


# TODO: migrate strategy


@external
def sweep(token: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, msg.sender, ERC20(token).balanceOf(self))