
# @version 0.2.12

"""
@title Unagii Vault V2
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20

interface UnagiiToken:
    def totalSupply(): nonpayable
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

# Adjust for each token PRECISION_MUL = 10 ** (18 - token.decimals)
PRECISION_MUL: constant(uint256) = 1

admin: public(address)
treasury: public(address)
timeLock: public(address)
guardian: public(address)
underlying: public(ERC20)
uToken: public(UnagiiToken)
paused: public(bool)
balanceInVault: public(uint256)
totalDebt: public(uint256)  # Amount of tokens that all strategies have borrowed

MAX_STRATEGIES: constant(uint256) = 10
strategies: public(HashMap[address, Strategy])
withdrawalQueue: public(address[MAX_STRATEGIES])


@external
def __init__(underlying: address, uToken: address, treasury: address, timeLock: address, guardian: address):
    self.admin = msg.sender
    self.treasury = treasury
    self.timeLock = timeLock
    self.guardian = guardian
    self.underlying = ERC20(underlying)
    self.uToken = UnagiiToken(uToken)

    self.paused = True

# utoken set minter
# v1.pause
# v1.deposit into migration strategy
# s approve v2 bal
# v2 transfer from s

# @external
# def transferFrom():
#     assert msg.sender = self.admin, "!admin"
#     self._safeTransfer(self.token, msg.sender, self, amount)


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


# # TODO: deposit log
# # TODO: deposit / withdraw block
# @external
# @nonreentrant("lock")
# def deposit(amount: uint256, minShares: uint256) -> uint256:
#     assert not self.paused, "paused"

#     _amount: uint256 = amount
#     if _amount == MAX_UINT256:
#         _amount = self.token.balanceOf(msg.sender)
#     assert _amount > 0, "deposit = 0"

#     # Actual amount transferred may be less than `_amount`,
#     # for example if token has fee on transfer
#     balBefore: uint256 = self.token.balanceOf(self)
#     self._safeTransferFrom(self.token.address, msg.sender, self, _amount)
#     balAfter: uint256 = self.token.balanceOf(self)
#     diff: uint256 = balAfter - balBefore

#     assert diff > 0, "diff = 0"

#     # s = shares to mint
#     # T = total shares before mint
#     # d = deposit amount
#     # A = total assets in vault + strategy before deposit
#     # s / (T + s) = d / (A + d)
#     # s = d / A * T

#     shares: uint256 = 0
#     # Saves 2 SLOADs (~4000 gas)
#     totalSupply: uint256 = self.totalSupply
#     if totalSupply > 0:
#         shares = PRECISION_MUL * diff * totalSupply / self._totalAssets() / PRECISION_MUL
#     else:
#         shares = diff
    
#     assert shares >= minShares, "shares < min"
    
#     self._mint(msg.sender, shares)
#     self.balanceInVault += diff

#     return shares

# # @view
# # @internal
# # def _shareValue(shares: uint256) -> uint256:
# #     # Returns price = 1:1 if vault is empty
# #     if self.totalSupply == 0:
# #         return shares

# #     # Determines the current value of `shares`.
# #         # NOTE: if sqrt(Vault.totalAssets()) >>> 1e39, this could potentially revert
# #     lockedFundsRatio: uint256 = (block.timestamp - self.lastReport) * self.lockedProfitDegration
# #     freeFunds: uint256 = self._totalAssets()
# #     precisionFactor: uint256 = self.precisionFactor
# #     if(lockedFundsRatio < DEGREDATION_COEFFICIENT):
# #         freeFunds -= (
# #             self.lockedProfit
# #              - (
# #                  precisionFactor
# #                  * lockedFundsRatio
# #                  * self.lockedProfit
# #                  / DEGREDATION_COEFFICIENT
# #                  / precisionFactor
# #              )
# #          )
# #     # NOTE: using 1e3 for extra precision here, when decimals is low
# #     return (
# #         precisionFactor
# #        * shares
# #         * freeFunds
# #         / self.totalSupply
# #         / precisionFactor
# #     )


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
# @external
# @nonreentrant("withdraw")
# def withdraw(shares: uint256, minAmount: uint256) -> uint256:
#     _shares: uint256 = shares
#     if _shares > self.balanceOf[msg.sender]:
#         _shares = self.balanceOf[msg.sender]
#     assert _shares > 0, "shares = 0"

#     # s = shares
#     # T = total supply of shares
#     # w = amount of underlying token to withdraw
#     # U = total amount of redeemable underlying token in vault + strategy
#     # s / T = w / U
#     # w = s / T * U

#     # TODO: degredation
#     amount: uint256 = 0
#     totalSupply: uint256 = self.totalSupply
#     if totalSupply > 0:
#         amount = PRECISION_MUL * shares * self._totalAssets() / totalSupply / PRECISION_MUL

#     totalLoss: uint256 = 0
#     # if value > self.token.balanceOf(self):
#     #     # We need to go get some from our strategies in the withdrawal queue
#     #     # NOTE: This performs forced withdrawals from each Strategy. During
#     #     #       forced withdrawal, a Strategy may realize a loss. That loss
#     #     #       is reported back to the Vault, and the will affect the amount
#     #     #       of tokens that the withdrawer receives for their shares. They
#     #     #       can optionally specify the maximum acceptable loss (in BPS)
#     #     #       to prevent excessive losses on their withdrawals (which may
#     #     #       happen in certain edge cases where Strategies realize a loss)
#     #     for strategy in self.withdrawalQueue:
#     #         if strategy == ZERO_ADDRESS:
#     #             break  # We've exhausted the queue

#     #         vault_balance: uint256 = self.token.balanceOf(self)
#     #         if value <= vault_balance:
#     #             break  # We're done withdrawing

#     #         amountNeeded: uint256 = value - vault_balance

#     #         # NOTE: Don't withdraw more than the debt so that Strategy can still
#     #         #       continue to work based on the profits it has
#     #         # NOTE: This means that user will lose out on any profits that each
#     #         #       Strategy in the queue would return on next harvest, benefiting others
#     #         amountNeeded = min(amountNeeded, self.strategies[strategy].totalDebt)
#     #         if amountNeeded == 0:
#     #             continue  # Nothing to withdraw from this Strategy, try the next one

#     #         # Force withdraw amount from each Strategy in the order set by governance
#     #         loss: uint256 = Strategy(strategy).withdraw(amountNeeded)
#     #         withdrawn: uint256 = self.token.balanceOf(self) - vault_balance

#     #         # NOTE: Withdrawer incurs any losses from liquidation
#     #         if loss > 0:
#     #             value -= loss
#     #             totalLoss += loss
#     #             self._reportLoss(strategy, loss)

#     #         # Reduce the Strategy's debt by the amount withdrawn ("realized returns")
#     #         # NOTE: This doesn't add to returns as it's not earned by "normal means"
#     #         self.strategies[strategy].totalDebt -= withdrawn
#     #         self.totalDebt -= withdrawn

#     # NOTE: We have withdrawn everything possible out of the withdrawal queue
#     #       but we still don't have enough to fully pay them back, so adjust
#     #       to the total amount we've freed up through forced withdrawals
#     # vault_balance: uint256 = self.token.balanceOf(self)
#     # if value > vault_balance:
#     #     value = vault_balance
#     #     # NOTE: Burn # of shares that corresponds to what Vault has on-hand,
#     #     #       including the losses that were incurred above during withdrawals
#     #     shares = self._sharesForAmount(value + totalLoss)

#     # NOTE: This loss protection is put in place to revert if losses from
#     #       withdrawing are more than what is considered acceptable.
#     # precisionFactor: uint256 = self.precisionFactor
#     # assert totalLoss <= precisionFactor * maxLoss * (value + totalLoss) / MAX_BPS / precisionFactor

#     # Burn shares (full value of what is being withdrawn)
#     self._burn(msg.sender, _shares)

#     assert amount >= minAmount, "amount < min"

#     balBefore: uint256 = self.token.balanceOf(self)
#     self._safeTransfer(self.token.address, msg.sender, amount)
#     balAfter: uint256 = self.token.balanceOf(self)
#     diff: uint256 = balAfter - balBefore

#     self.balanceInVault -= diff

#     # self.safeTransfer(self.token.address, recipient, value)

#     return diff


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
# def _pop():
#     for i in range(MAX_STRATEGIES):
#         j: uint256 = MAX_STRATEGIES - 1 - i
#         strat: address = self.withdrawalQueue[j]
#         if strat != ZERO_ADDRESS:
#             self.withdrawalQueue[j] = ZERO_ADDRESS
#             break
#     raise "empty array"


# @internal
# def _remove(i: uint256):
#     # range(i, MAX_STRATEGIES) does not compile
#     for j in range(MAX_STRATEGIES - 1):
#         if j < i:
#             continue
#         self.withdrawalQueue[j] = self.withdrawalQueue[j + 1]
#     self._pop()
    

# @external
# def addStrategyToQueue(strategy: address):
#     assert msg.sender == self.admin, "!admin"
#     assert self.strategies[strategy].approved, "!approved"

#     # Check strategy not in queue and append
#     i: uint256 = 0
#     for strat in self.withdrawalQueue:
#         if strat == ZERO_ADDRESS:
#             break
#         assert strat != strategy, "active" 
#         i += 1
#     assert i < MAX_STRATEGIES, "active > max"

#     self.withdrawalQueue[i] = strategy

#     log AddStrategyToQueue(strategy)



# @external
# def removeStrategyFromQueue(strategy: address):
#     assert msg.sender == self.admin, "!admin"

#     for i in range(MAX_STRATEGIES):
#         strat: address = self.withdrawalQueue[i]
#         if strat == strategy:
#             self._remove(i)

#     log RemoveStrategyFromQueue(strategy)

# migration

# u = underlying token
# ut = unagi token
# v1 = vault 1
# v2 = vault 2

# v2.pause
# v1.pause
# ut.setMinter(v2)
# u.approve(v2, bal of v1, {from: v1})
# u.transferFrom(v1, v2, bal of v1, {from: v2})

@external
def sweep(token: address):
    assert msg.sender == self.admin, "!admin"
    assert token != self.underlying.address, "protected token"
    self._safeTransfer(token, self.admin, ERC20(token).balanceOf(self))
