
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


interface IStrategy:
    def vault() -> address: view
    def token() -> address: view

event ApproveStrategy:
    strategy: indexed(address)

event RevokeStrategy:
    strategy: indexed(address)

event AddStrategyToQueue:
    strategy: indexed(address)

event RemoveStrategyFromQueue:
    strategy: indexed(address)

struct Strategy:
    approved: bool
    debt: uint256

# TODO: remove?
# https://github.com/yearn/yearn-vaults/issues/333
# Adjust for each token PRECISION_MUL = 10 ** (18 - token.decimals)
PRECISION_MUL: constant(uint256) = 1

admin: public(address)
timeLock: public(address)
guardian: public(address)
token: public(ERC20)
uToken: public(UnagiiToken)
paused: public(bool)
balanceInVault: public(uint256)
totalDebt: public(uint256)  # Amount of tokens that all strategies have borrowed

MAX_STRATEGIES: constant(uint256) = 20
withdrawalQueue: public(address[MAX_STRATEGIES])

strategies: public(HashMap[address, Strategy])


@external
def __init__(token: address, uToken: address):
    self.admin = msg.sender
    self.timeLock = msg.sender
    self.guardian = msg.sender
    self.token = ERC20(token)
    self.uToken = UnagiiToken(uToken)

    decimals: uint256 = DetailedERC20(self.token.address).decimals()
    if decimals < 18:
        assert PRECISION_MUL == 18 - decimals, "precision != 18 - decimals"
    else:
        assert PRECISION_MUL == 1, "precision != 1"

    assert self.uToken.token() == self.token.address, "uToken.token != token"

    self.paused = True


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


@view
@internal
def _totalAssets() -> uint256:
    return self.balanceInVault + self.totalDebt


@view
@external
def totalAssets() -> uint256:
    return self._totalAssets()


# TODO:
# @view
# @external
# def pricePerShare() -> uint256:
#     totalSupply: uint256 = self.uToken.totalSupply()
#     totalAssets: uint256 = self._totalAssets()

#     if totalSupply > 0:
#         return 
    
#     return 10 ** ERC20Detail(self.token.address).decimals()


# TODO: deposit log
# TODO: deposit / withdraw block
@external
@nonreentrant("lock")
def deposit(amount: uint256, minShares: uint256) -> uint256:
    assert not self.paused, "paused"

    _amount: uint256 = amount
    if _amount == MAX_UINT256:
        _amount = self.token.balanceOf(msg.sender)
    assert _amount > 0, "deposit = 0"

    # Actual amount transferred may be less than `_amount`,
    # for example if token has fee on transfer
    balBefore: uint256 = self.token.balanceOf(self)
    self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
    balAfter: uint256 = self.token.balanceOf(self)
    diff: uint256 = balAfter - balBefore

    assert diff > 0, "diff = 0"

    # s = shares to mint
    # T = total shares before mint
    # d = deposit amount
    # A = total assets in vault + strategy before deposit
    # s / (T + s) = d / (A + d)
    # s = d / A * T

    shares: uint256 = 0
    totalSupply: uint256 = self.uToken.totalSupply()
    if totalSupply > 0:
        shares = PRECISION_MUL * diff * totalSupply / self._totalAssets() / PRECISION_MUL
    else:
        shares = diff
    
    assert shares >= minShares, "shares < min"
    
    self.uToken.mint(msg.sender, shares)
    self.balanceInVault += diff

    return shares

DEGREDATION_COEFFICIENT: constant(uint256) = 10 ** 18

lastReport: public(uint256)  # block.timestamp of last report
lockedProfit: public(uint256) # how much profit is locked and cant be withdrawn
lockedProfitDegration: public(uint256) # rate per block of degration. DEGREDATION_COEFFICIENT is 100% per block

@external
def setLockedProfitDegration(degration: uint256):
    """
    @notice
        Changes the locked profit degration.
    @param degration The rate of degration in percent per second scaled to 1e18.
    """
    assert msg.sender == self.admin, "!admin"
    assert degration <= DEGREDATION_COEFFICIENT, "degration > max"
    self.lockedProfitDegration = degration


@view
@internal
def _shareValue(shares: uint256) -> uint256:
    # Returns price = 1:1 if vault is empty
    totalSupply: uint256 = self.uToken.totalSupply()
    if totalSupply == 0:
        return shares

    # Determines the current value of `shares`.
        # NOTE: if sqrt(Vault.totalAssets()) >>> 1e39, this could potentially revert
    lockedFundsRatio: uint256 = (block.timestamp - self.lastReport) * self.lockedProfitDegration
    freeFunds: uint256 = self._totalAssets()
    if lockedFundsRatio < DEGREDATION_COEFFICIENT:
        freeFunds -= (
            self.lockedProfit
             - (
                 PRECISION_MUL
                 * lockedFundsRatio
                 * self.lockedProfit
                 / DEGREDATION_COEFFICIENT
                 / PRECISION_MUL
             )
         )

    # s = shares
    # T = total supply of shares
    # w = amount of token token to withdraw
    # U = total amount of redeemable token token in vault + strategy
    # s / T = w / U
    # w = s / T * U

    return PRECISION_MUL * shares * freeFunds / totalSupply / PRECISION_MUL


@view
@external
def pricePerShare() -> uint256:
    """
    @notice Gives the price for a single Vault share.
    @dev See dev note on `withdraw`.
    @return The value of a single share.
    """
    return self._shareValue(10 ** self.uToken.decimals())

# # @view
# # @internal
# # def _sharesForAmount(amount: uint256) -> uint256:
# #     # Determines how many shares `amount` of token would receive.
# #     # See dev note on `deposit`.
# #     if self._totalAssets() > 0:
# #         # NOTE: if sqrt(token.totalSupply()) > 1e37, this could potentially revert
# #         precisionFactor: uint256 = self.precisionFactor
# #         return  (
# #             precisionFactor
# #             * amount
# #             * self.totalSupply
# #             / self._totalAssets()
# #             / precisionFactor
# #         )
# #     else:
# #         return 0


# # @view
# # @external
# # def maxAvailableShares() -> uint256:
# #     """
# #     @notice
# #         Determines the maximum quantity of shares this Vault can facilitate a
# #         withdrawal for, factoring in assets currently residing in the Vault,
# #         as well as those deployed to strategies on the Vault's balance sheet.
# #     @dev
# #         Regarding how shares are calculated, see dev note on `deposit`.
# #         If you want to calculated the maximum a user could withdraw up to,
# #         you want to use this function.
# #         Note that the amount provided by this function is the theoretical
# #         maximum possible from withdrawing, the real amount depends on the
# #         realized losses incurred during withdrawal.
# #     @return The total quantity of shares this Vault can provide.
# #     """
# #     shares: uint256 = self._sharesForAmount(self.token.balanceOf(self))

# #     for strategy in self.withdrawalQueue:
# #         if strategy == ZERO_ADDRESS:
# #             break
# #         shares += self._sharesForAmount(self.strategies[strategy].totalDebt)

# #     return shares


# # TODO: withdraw log
@external
@nonreentrant("withdraw")
def withdraw(shares: uint256, minAmount: uint256) -> uint256:
    _shares: uint256 = shares
    _bal: uint256 = self.uToken.balanceOf(msg.sender)
    if _shares > _bal:
        _shares = _bal
    assert _shares > 0, "shares = 0"

    amount: uint256 = self._shareValue(_shares)

    totalLoss: uint256 = 0
    # if value > self.token.balanceOf(self):
    #     # We need to go get some from our strategies in the withdrawal queue
    #     # NOTE: This performs forced withdrawals from each Strategy. During
    #     #       forced withdrawal, a Strategy may realize a loss. That loss
    #     #       is reported back to the Vault, and the will affect the amount
    #     #       of tokens that the withdrawer receives for their shares. They
    #     #       can optionally specify the maximum acceptable loss (in BPS)
    #     #       to prevent excessive losses on their withdrawals (which may
    #     #       happen in certain edge cases where Strategies realize a loss)
    #     for strategy in self.withdrawalQueue:
    #         if strategy == ZERO_ADDRESS:
    #             break  # We've exhausted the queue

    #         vault_balance: uint256 = self.token.balanceOf(self)
    #         if value <= vault_balance:
    #             break  # We're done withdrawing

    #         amountNeeded: uint256 = value - vault_balance

    #         # NOTE: Don't withdraw more than the debt so that Strategy can still
    #         #       continue to work based on the profits it has
    #         # NOTE: This means that user will lose out on any profits that each
    #         #       Strategy in the queue would return on next harvest, benefiting others
    #         amountNeeded = min(amountNeeded, self.strategies[strategy].totalDebt)
    #         if amountNeeded == 0:
    #             continue  # Nothing to withdraw from this Strategy, try the next one

    #         # Force withdraw amount from each Strategy in the order set by governance
    #         loss: uint256 = Strategy(strategy).withdraw(amountNeeded)
    #         withdrawn: uint256 = self.token.balanceOf(self) - vault_balance

    #         # NOTE: Withdrawer incurs any losses from liquidation
    #         if loss > 0:
    #             value -= loss
    #             totalLoss += loss
    #             self._reportLoss(strategy, loss)

    #         # Reduce the Strategy's debt by the amount withdrawn ("realized returns")
    #         # NOTE: This doesn't add to returns as it's not earned by "normal means"
    #         self.strategies[strategy].totalDebt -= withdrawn
    #         self.totalDebt -= withdrawn

    # NOTE: We have withdrawn everything possible out of the withdrawal queue
    #       but we still don't have enough to fully pay them back, so adjust
    #       to the total amount we've freed up through forced withdrawals
    # vault_balance: uint256 = self.token.balanceOf(self)
    # if value > vault_balance:
    #     value = vault_balance
    #     # NOTE: Burn # of shares that corresponds to what Vault has on-hand,
    #     #       including the losses that were incurred above during withdrawals
    #     shares = self._sharesForAmount(value + totalLoss)

    # NOTE: This loss protection is put in place to revert if losses from
    #       withdrawing are more than what is considered acceptable.
    # precisionFactor: uint256 = self.precisionFactor
    # assert totalLoss <= precisionFactor * maxLoss * (value + totalLoss) / MAX_BPS / precisionFactor

    # Burn shares (full value of what is being withdrawn)
    self.uToken.burn(msg.sender, _shares)

    assert amount >= minAmount, "amount < min"

    balBefore: uint256 = self.token.balanceOf(self)
    self._safeTransfer(self.token.address, msg.sender, amount)
    balAfter: uint256 = self.token.balanceOf(self)
    diff: uint256 = balAfter - balBefore

    self.balanceInVault -= diff

    # self.safeTransfer(self.token.address, recipient, value)

    return diff

@external
def approveStrategy(strategy: address):
    assert not self.paused, "paused"
    assert msg.sender == self.timeLock, "!time lock"

    assert not self.strategies[strategy].approved, "approved"
    assert IStrategy(strategy).vault() == self, "strategy.vault != vault"
    assert IStrategy(strategy).token() == self.token.address, "strategy.token != token"

    self.strategies[strategy] = Strategy({
        approved: True,
        debt: 0
    })
    log ApproveStrategy(strategy)


@external
def revokeStrategy(strategy: address):
    assert msg.sender == self.admin, "!admin"
    assert self.strategies[strategy].approved, "!approved"
    assert strategy not in self.withdrawalQueue, "active"

    self.strategies[strategy].approved = False
    log RevokeStrategy(strategy)


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
def addStrategyToQueue(strategy: address):
    assert msg.sender == self.admin, "!admin"
    assert self.strategies[strategy].approved, "!approved"
    assert strategy not in self.withdrawalQueue, "active"

    self._append(strategy)
    log AddStrategyToQueue(strategy)


@external
def removeStrategyFromQueue(strategy: address):
    assert msg.sender == self.admin, "!admin"
    assert strategy in self.withdrawalQueue, "!active"

    i: uint256 = self._find(strategy)
    self._remove(i)
    log RemoveStrategyFromQueue(strategy)


@external
def borrow(amount: uint256):
    pass


@external
def repay(amount: uint256):
    pass


@external
def sync():
    pass



# migration

# u = token token
# ut = unagi token
# v1 = vault 1
# v2 = vault 2

# v2.pause
# v1.pause
# ut.setMinter(v2)
# u.approve(v2, bal of v1, {from: v1})
# u.transferFrom(v1, v2, bal of v1, {from: v2})

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
