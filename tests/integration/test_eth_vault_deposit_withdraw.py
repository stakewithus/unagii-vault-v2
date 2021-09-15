import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy
from brownie import StrategyEthTest

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

    def __init__(cls, setup, vault, admin, treasury, uToken, eth_whale):
        timeLock = vault.timeLock()

        cls.vault = vault
        cls.uToken = uToken
        cls.admin = admin
        cls.eth_whale = eth_whale

        cls.strategies = []
        for i in range(N):
            min_tvl = 100
            max_tvl = 10000
            strat = StrategyEthTest.deploy(
                vault, treasury, min_tvl, max_tvl, {"from": admin}
            )

            vault.approveStrategy(strat, {"from": timeLock})
            vault.activateStrategy(strat, 1, {"from": timeLock})

            cls.strategies.append(strat)

    def setup(self):
        self.totalAssets = 0
        self.totalDebt = 0

    def rule_deposit(self, user, deposit_amount):
        print("deposit", user, deposit_amount)

        self.eth_whale.transfer(user, deposit_amount)

        totalSupply = self.uToken.totalSupply()
        free = self.vault.calcFreeFunds()

        if totalSupply > 0 and free == 0:
            with brownie.reverts():
                self.vault.deposit(0, {"from": user, "value": deposit_amount})
        else:
            self.vault.deposit(0, {"from": user, "value": deposit_amount})
            self.totalAssets += deposit_amount

    def rule_withdraw(self, user, shares_to_withdraw, loss):
        shares = min(shares_to_withdraw, self.uToken.balanceOf(user))

        if shares > 0:
            bal = self.vault.balance()
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
                                strat._burn_(burn)
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
                self.vault.balance(),
                "strategy",
                i,
            )

            self.vault.borrow(borrow, {"from": strat})
            self.totalDebt += borrow

    def rule_repay(self, repay_amount, j):
        strat = self.strategies[j]
        debt = self.vault.strategies(strat)["debt"]
        repay = min(repay_amount, debt, strat.balance())

        if repay > 0:
            print("repay", repay, "debt", debt, j)

            self.vault.repay({"from": strat, "value": repay})
            self.totalDebt -= repay

    def rule_sync_gain(self, gain, k):
        strat = self.strategies[k]

        print("gain", gain, "strategy", k)
        self.eth_whale.transfer(strat, gain)

        self.vault.sync(strat, 0, 2 ** 256 - 1, {"from": self.admin})

        self.totalAssets += gain
        self.totalDebt += gain

    def rule_sync_loss(self, loss, k):
        strat = self.strategies[k]
        debt = self.vault.strategies(strat)["debt"]
        _loss = min(loss, debt, strat.balance())

        if _loss > 0:
            print("loss", _loss)

            strat._burn_(_loss)
            self.vault.sync(strat, 0, 2 ** 256 - 1, {"from": self.admin})

            self.totalAssets -= _loss
            self.totalDebt -= _loss

    def invariant(self):
        assert self.totalAssets == self.vault.balance() + self.vault.totalDebt()
        assert self.vault.totalDebt() == self.totalDebt


def test_stateful(setup_eth, ethVault, admin, treasury, uEth, eth_whale, state_machine):
    state_machine(StateMachine, setup_eth, ethVault, admin, treasury, uEth, eth_whale)
