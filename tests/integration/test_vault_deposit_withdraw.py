import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy
from brownie import StrategyTest

# number of active strategies
N = 5


class StateMachine:
    user = strategy("address", exclude=ZERO_ADDRESS)
    deposit_amount = strategy("uint256", min_value=1, max_value=1000)
    shares_to_withdraw = strategy("uint256", min_value=1, max_value=1000)
    borrow_amount = strategy("uint256", min_value=1)
    repay_amount = strategy("uint256", min_value=1)
    # index of strategy that will borrow
    i = strategy("uint256", min_value=0, max_value=N - 1)
    # index of strategy that will repay
    j = strategy("uint256", min_value=0, max_value=N - 1)
    # index of strategy that will sync
    k = strategy("uint256", min_value=0, max_value=N - 1)
    gain = strategy("uint256", min_value=1, max_value=1000)
    loss = strategy("uint256", min_value=1)

    def __init__(cls, setup, vault, admin, treasury, token, uToken):
        timeLock = vault.timeLock()

        cls.vault = vault
        cls.token = token
        cls.uToken = uToken
        cls.admin = admin

        cls.strategies = []
        for i in range(N):
            strat = StrategyTest.deploy(token, vault, treasury, {"from": admin})

            vault.approveStrategy(strat, {"from": timeLock})
            vault.activateStrategy(strat, 1, {"from": timeLock})

            cls.strategies.append(strat)

    def setup(self):
        self.totalAssets = 0
        self.totalDebt = 0

    def rule_deposit(self, user, deposit_amount):
        print("deposit", user, deposit_amount)

        self.token.mint(user, deposit_amount)
        self.token.approve(self.vault, deposit_amount, {"from": user})

        totalSupply = self.uToken.totalSupply()
        free = self.vault.calcFreeFunds()

        if totalSupply > 0 and free == 0:
            with brownie.reverts():
                self.vault.deposit(deposit_amount, 0, {"from": user})
        else:
            self.vault.deposit(deposit_amount, 0, {"from": user})
            self.totalAssets += deposit_amount

    def rule_withdraw(self, user, shares_to_withdraw, loss):
        shares = min(shares_to_withdraw, self.uToken.balanceOf(user))

        if shares > 0:
            bal = self.token.balanceOf(self.vault)
            totalDebt = self.vault.totalDebt()
            calc = self.vault.calcWithdraw(shares)

            _loss = min(loss, totalDebt)
            if calc >= bal:
                _loss = min(_loss, calc - bal)

            print(
                "withdraw",
                user,
                "shares",
                shares,
                "calc",
                calc,
                "bal",
                bal,
                "total debt",
                totalDebt,
                "loss",
                _loss,
            )

            if bal >= calc:
                # no loss
                self.totalAssets -= calc
            else:
                if _loss > 0:
                    ## simulate withdraw ##
                    # amount to withdraw
                    a = calc
                    # balance of vault
                    b = bal
                    # burn from strategies
                    l = _loss
                    for i in range(N):
                        strat = self.strategies[i]

                        if b >= a:
                            break

                        debt = self.vault.strategies(strat)["debt"]
                        total = strat.totalAssets()
                        w = min(a - b, debt, total)
                        if w > 0:
                            pass
                            # simulate loss
                            if l > 0:
                                burn = min(l, total)
                                self.token.burn(strat, burn)
                                l -= burn
                                a -= burn
                                self.totalDebt -= burn
                                # strategy cannot return need
                                if w > total - burn:
                                    w = total - burn
                        b += w
                        self.totalDebt -= w

                        print(
                            i,
                            "bal",
                            b,
                            "w",
                            w,
                            "debt",
                            debt,
                            "total",
                            total,
                            "l",
                            l,
                        )
                    self.totalAssets -= calc
                else:
                    self.totalAssets -= calc
                    self.totalDebt -= calc - bal

            self.vault.withdraw(shares, 0, {"from": user})

    def rule_borrow(self, borrow_amount, i):
        strat = self.strategies[i]
        available = self.vault.calcMaxBorrow(strat)
        borrow = min(borrow_amount, available)

        if borrow > 0:
            print(
                "borrow",
                borrow,
                "availabe",
                available,
                "bal",
                self.token.balanceOf(self.vault),
                "strategy",
                i,
            )

            self.vault.borrow(borrow, {"from": strat})
            self.totalDebt += borrow

    def rule_repay(self, repay_amount, j):
        strat = self.strategies[j]
        debt = self.vault.strategies(strat)["debt"]
        repay = min(repay_amount, debt, self.token.balanceOf(strat))

        if repay > 0:
            print("repay", repay, "debt", debt, j)

            self.vault.repay(repay, {"from": strat})
            self.totalDebt -= repay

    def rule_sync_gain(self, gain, k):
        strat = self.strategies[k]

        print("gain", gain, "strategy", k)
        self.token.mint(strat, gain)

        self.vault.sync(strat, 0, 2 ** 256 - 1, {"from": self.admin})

        self.totalAssets += gain
        self.totalDebt += gain

    def rule_sync_loss(self, loss, k):
        strat = self.strategies[k]
        debt = self.vault.strategies(strat)["debt"]
        _loss = min(loss, debt, self.token.balanceOf(strat))

        if _loss > 0:
            print("loss", _loss)

            self.token.burn(strat, _loss)
            self.vault.sync(strat, 0, 2 ** 256 - 1, {"from": self.admin})

            self.totalAssets -= _loss
            self.totalDebt -= _loss

    def invariant(self):
        assert (
            self.totalAssets
            == self.token.balanceOf(self.vault) + self.vault.totalDebt()
        )
        assert self.vault.totalDebt() == self.totalDebt


def test_stateful(setup, vault, admin, treasury, token, uToken, state_machine):
    state_machine(
        StateMachine,
        setup,
        vault,
        admin,
        treasury,
        token,
        uToken,
    )
