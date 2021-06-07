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
    def withdraw(amount: uint256) -> uint256: nonpayable
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
    totalGain: uint256
    totalLoss: uint256
    perfFee: uint256
    minDebtPerHarvest: uint256
    maxDebtPerHarvest: uint256


event SetNextAdmin:
    nextAdmin: address


event AcceptAdmin:
    admin: address


event SetGuardian:
    guardian: address


event SetKeeper:
    keeper: address


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

vault: public(Vault)
token: public(ERC20)
admin: public(address)
nextAdmin: public(address)
guardian: public(address) # TODO: remove?
keeper: public(address)

strategies: public(HashMap[address, Strategy])
queue: public(address[MAX_QUEUE])


@external
def __init__(
    token: address,
    guardian: address,
    keeper: address
):
    self.admin = msg.sender
    self.guardian = guardian
    self.keeper = keeper
    self.token = ERC20(token)


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
    assert msg.sender in [self.admin, self.guardian, self.keeper], "!auth"
    self.guardian = guardian
    log SetGuardian(guardian)


@external
def setKeeper(keeper: address):
    assert msg.sender in [self.admin, self.guardian, self.keeper], "!auth"
    self.keeper = keeper
    log SetKeeper(keeper)


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

# @internal
# @view
# def _calcOutstandingDebt() -> uint256:
#     if self.paused:
#         return self.debt

#     freeFunds: uint256 = self._calcFreeFunds()
#     limit: uint256 = (MAX_MIN_RESERVE - self.minReserve) * freeFunds / MAX_MIN_RESERVE
#     debt: uint256 = self.debt

#     if debt >= limit:
#         return debt - limit
#     return 0


# # TODO: test
# @external
# def calcOutstandingDebt() -> uint256:
#     return self._calcOutstandingDebt()

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
    assert msg.sender in [self.admin, self.guardian], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"

    # TODO: if strategy.debt > 0?
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
    assert msg.sender == self.admin, "!admin"

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


@external
def updateStrategyPerformanceFee(strategy: address, perfFee: uint256):
    assert msg.sender == self.admin, "!admin"
    assert self.strategies[strategy].approved, "!approved"
    assert perfFee <= MAX_PERF_FEE, "perf fee > max"
    self.strategies[strategy].perfFee = perfFee
    log UpdateStrategyPerformanceFee(strategy, perfFee)


@external
def sweep(token: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, msg.sender, ERC20(token).balanceOf(self))