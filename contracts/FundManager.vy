# @version 0.2.12

"""
@title Unagii FundManager
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

# TODO: comment


interface Vault:
    def token() -> address: view
    def debt() -> uint256: view
    def borrow(amount: uint256) -> uint256: nonpayable
    def repay(amount: uint256) -> uint256: nonpayable
    def report(gain: uint256, loss: uint256): nonpayable


interface IStrategy:
    def fundManager() -> address: view
    def token() -> address: view
    def withdraw(amount: uint256) -> uint256: nonpayable
    # TODO: migrate
    def migrate(newVersion: address): nonpayable


MAX_QUEUE: constant(uint256) = 20


struct Strategy:
    approved: bool
    active: bool
    activated: bool
    debtRatio: uint256
    debt: uint256
    minBorrow: uint256
    maxBorrow: uint256


event SetNextTimeLock:
    nextTimeLock: address


event AcceptTimeLock:
    timeLock: address


event SetAdmin:
    admin: address


event SetGuardian:
    guardian: address


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


event SetDebtRatios:
    debtRatios: uint256[MAX_QUEUE]


event SetMinMaxBorrow:
    strategy: indexed(address)
    minBorrow: uint256
    maxBorrow: uint256


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


event Withdraw:
    vault: indexed(address)
    amount: uint256
    actual: uint256
    loss: uint256


event WithdrawStrategy:
    strategy: indexed(address)
    need: uint256
    loss: uint256
    diff: uint256


event Borrow:
    strategy: indexed(address)
    amount: uint256
    borrowed: uint256


event Repay:
    strategy: indexed(address)
    amount: uint256
    repaid: uint256


event Report:
    strategy: indexed(address)
    gain: uint256
    loss: uint256
    debt: uint256


vault: public(Vault)
token: public(ERC20)
# privileges - time lock >= admin >= guardian, worker
timeLock: public(address)
nextTimeLock: public(address)
admin: public(address)
guardian: public(address)
worker: public(address)

paused: public(bool)
totalDebt: public(uint256)
MAX_TOTAL_DEBT_RATIO: constant(uint256) = 10000
totalDebtRatio: public(uint256)
strategies: public(HashMap[address, Strategy])
queue: public(address[MAX_QUEUE])


@external
def __init__(token: address, guardian: address, worker: address):
    self.token = ERC20(token)
    self.timeLock = msg.sender
    self.admin = msg.sender
    self.guardian = guardian
    self.worker = worker


# TODO: migrate


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


@external
def setWorker(worker: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    self.worker = worker
    log SetWorker(worker)


@external
def setPause(paused: bool):
    assert msg.sender in [self.timeLock, self.admin, self.guardian], "!auth"
    self.paused = paused
    log SetPause(paused)


@internal
def _safeApprove(token: address, spender: address, amount: uint256):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("approve(address,uint256)"),
            convert(spender, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(res) > 0:
        assert convert(res, bool), "approve failed"


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


# TODO: test migration
@external
def setVault(vault: address):
    assert msg.sender == self.timeLock, "!time lock"
    assert Vault(vault).token() == self.token.address, "vault token != token"

    if self.vault.address != ZERO_ADDRESS:
        self._safeApprove(self.token.address, self.vault.address, 0)

    self.vault = Vault(vault)
    self._safeApprove(self.token.address, self.vault.address, MAX_UINT256)
    # TODO: reset total debt?
    log SetVault(vault)


@internal
@view
def _totalAssets() -> uint256:
    return self.token.balanceOf(self) + self.totalDebt


@external
@view
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
def approveStrategy(strategy: address):
    assert msg.sender == self.timeLock, "!time lock"

    assert not self.strategies[strategy].approved, "approved"
    assert IStrategy(strategy).fundManager() == self, "strategy fund manager != this"
    assert IStrategy(strategy).token() == self.token.address, "strategy token != token"

    self.strategies[strategy] = Strategy({
        approved: True,
        active: False,
        activated: False,
        debtRatio: 0,
        debt: 0,
        minBorrow: 0,
        maxBorrow: 0,
    })

    log ApproveStrategy(strategy)


@external
def revokeStrategy(strategy: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"

    # TODO: assert strategy.debt > 0 ?
    self.strategies[strategy].approved = False
    log RevokeStrategy(strategy)


@external
def addStrategyToQueue(
    strategy: address, debtRatio: uint256, minBorrow: uint256, maxBorrow: uint256
):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert not self.strategies[strategy].active, "active"
    assert self.totalDebtRatio + debtRatio <= MAX_TOTAL_DEBT_RATIO, "ratio > max"
    assert minBorrow <= maxBorrow, "min borrow > max borrow"

    self._append(strategy)
    self.strategies[strategy].active = True
    self.strategies[strategy].activated = True
    self.strategies[strategy].debtRatio = debtRatio
    self.strategies[strategy].minBorrow = minBorrow
    self.strategies[strategy].maxBorrow = maxBorrow
    self.totalDebtRatio += debtRatio

    log AddStrategyToQueue(strategy)


@external
def removeStrategyFromQueue(strategy: address):
    assert msg.sender in [self.timeLock, self.admin, self.guardian], "!auth"
    assert self.strategies[strategy].active, "!active"

    self._remove(self._find(strategy))
    self.strategies[strategy].active = False
    self.totalDebtRatio -= self.strategies[strategy].debtRatio
    self.strategies[strategy].debtRatio = 0

    log RemoveStrategyFromQueue(strategy)


@external
def setQueue(queue: address[MAX_QUEUE]):
    assert msg.sender in [self.timeLock, self.admin], "!auth"

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
def setDebtRatios(debtRatios: uint256[MAX_QUEUE]):
    assert msg.sender in [self.timeLock, self.admin], "!auth"

    # check that we're only setting debt ratio on active strategy
    for i in range(MAX_QUEUE):
        if self.queue[i] == ZERO_ADDRESS:
            assert debtRatios[i] == 0, "debt ratio != 0"

    # use memory to save gas
    totalDebtRatio: uint256 = 0
    for i in range(MAX_QUEUE):
        addr: address = self.queue[i]
        if addr == ZERO_ADDRESS:
            break

        debtRatio: uint256 = debtRatios[i]
        self.strategies[addr].debtRatio = debtRatio
        totalDebtRatio += debtRatio

    self.totalDebtRatio = totalDebtRatio

    assert self.totalDebtRatio <= MAX_TOTAL_DEBT_RATIO, "total > max"

    log SetDebtRatios(debtRatios)


@external
def setMinMaxBorrow(strategy: address, minBorrow: uint256, maxBorrow: uint256):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert self.strategies[strategy].approved, "!approved"
    assert minBorrow <= maxBorrow, "min borrow > max borrow"

    self.strategies[strategy].minBorrow = minBorrow
    self.strategies[strategy].maxBorrow = maxBorrow

    log SetMinMaxBorrow(strategy, minBorrow, maxBorrow)


# functions between Vault and this contract #
@external
def borrowFromVault(amount: uint256, _min: uint256):
    assert msg.sender in [self.timeLock, self.admin, self.worker], "!auth"
    # fails if vault not set
    borrowed: uint256 = self.vault.borrow(amount)
    assert borrowed >= _min, "borrowed < min"

    log BorrowFromVault(self.vault.address, amount, borrowed)


@external
def repayVault(amount: uint256, _min: uint256):
    assert msg.sender in [self.timeLock, self.admin, self.worker], "!auth"
    # fails if vault not set
    # infinite approved in setVault()
    repaid: uint256 = self.vault.repay(amount)
    assert repaid >= _min, "repaid < min"

    log RepayVault(self.vault.address, amount, repaid)


# _min and _max to protect against price manipulation
@external
def reportToVault(_min: uint256, _max: uint256):
    assert msg.sender in [self.timeLock, self.admin, self.worker], "!auth"

    total: uint256 = self._totalAssets()
    assert total >= _min and total <= _max, "total not in range"

    debt: uint256 = self.vault.debt()
    gain: uint256 = 0
    loss: uint256 = 0

    if total > debt:
        gain = min(total - debt, self.token.balanceOf(self))
    else:
        loss = debt - total

    if gain > 0 or loss > 0:
        self.vault.report(gain, loss)

    log ReportToVault(self.vault.address, total, debt, gain, loss)


# functions between vault -> this contract -> strategies #
@internal
def _withdraw(amount: uint256) -> uint256:
    _amount: uint256 = amount
    totalLoss: uint256 = 0
    for strategy in self.queue:
        if strategy == ZERO_ADDRESS:
            break

        bal: uint256 = self.token.balanceOf(self)
        if _amount <= bal:
            break

        debt: uint256 = self.strategies[strategy].debt
        need: uint256 = min(_amount - bal, debt)
        if need == 0:
            continue

        diff: uint256 = self.token.balanceOf(self)
        loss: uint256 = IStrategy(strategy).withdraw(need)
        diff = self.token.balanceOf(self) - diff

        if loss > 0:
            _amount -= loss
            totalLoss += loss
            self.strategies[strategy].debt -= loss
            self.totalDebt -= loss

        self.strategies[strategy].debt -= diff
        self.totalDebt -= diff

        log WithdrawStrategy(strategy, need, loss, diff)

    return totalLoss


@external
def withdraw(amount: uint256) -> uint256:
    assert msg.sender == self.vault.address, "!vault"
    assert amount > 0, "withdraw = 0"

    _amount: uint256 = amount
    bal: uint256 = self.token.balanceOf(self)
    loss: uint256 = 0
    if _amount > bal:
        # try to withdraw until balance of fund manager >= _amount
        loss = self._withdraw(_amount)
        _amount = min(_amount - loss, self.token.balanceOf(self))

    self._safeTransfer(self.token.address, msg.sender, _amount)

    log Withdraw(msg.sender, amount, _amount, loss)

    return loss


# functions between this contract and strategies #
@internal
@view
def _calcMaxBorrow(strategy: address) -> uint256:
    if self.paused or self.totalDebtRatio == 0:
        return 0

    # strategy debtRatio > 0 only if strategy is active
    limit: uint256 = (
        self.strategies[strategy].debtRatio * self._totalAssets() / self.totalDebtRatio
    )
    debt: uint256 = self.strategies[strategy].debt

    if debt >= limit:
        return 0

    available: uint256 = min(limit - debt, self.token.balanceOf(self))

    if available < self.strategies[strategy].minBorrow:
        return 0
    else:
        return min(available, self.strategies[strategy].maxBorrow)


@external
@view
def calcMaxBorrow(strategy: address) -> uint256:
    return self._calcMaxBorrow(strategy)


@external
@view
def getDebt(strategy: address) -> uint256:
    return self.strategies[strategy].debt


@external
def borrow(amount: uint256) -> uint256:
    assert not self.paused, "paused"
    assert self.strategies[msg.sender].active, "!active"

    _amount: uint256 = min(amount, self._calcMaxBorrow(msg.sender))
    assert _amount > 0, "borrow = 0"

    self._safeTransfer(self.token.address, msg.sender, _amount)

    # include any fee on transfer to debt
    self.strategies[msg.sender].debt += _amount
    self.totalDebt += _amount

    log Borrow(msg.sender, amount, _amount)

    return _amount


@external
def repay(amount: uint256) -> uint256:
    assert self.strategies[msg.sender].approved, "!approved"

    _amount: uint256 = min(amount, self.strategies[msg.sender].debt)
    assert _amount > 0, "repay = 0"

    diff: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
    diff = self.token.balanceOf(self) - diff

    # exclude fee on transfer from debt payment
    self.strategies[msg.sender].debt -= diff
    self.totalDebt -= diff

    log Repay(msg.sender, amount, diff)

    return diff


@external
def report(gain: uint256, loss: uint256):
    assert self.strategies[msg.sender].active, "!active"
    # can't have both gain and loss > 0
    assert (gain >= 0 and loss == 0) or (gain == 0 and loss >= 0), "gain and loss > 0"

    if gain > 0:
        self._safeTransferFrom(self.token.address, msg.sender, self, gain)
    elif loss > 0:
        self.strategies[msg.sender].debt -= loss
        self.totalDebt -= loss

    log Report(msg.sender, gain, loss, self.strategies[msg.sender].debt)


# TODO: migrate strategy


@external
def sweep(token: address):
    assert msg.sender in [self.timeLock, self.admin], "!auth"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, msg.sender, ERC20(token).balanceOf(self))
