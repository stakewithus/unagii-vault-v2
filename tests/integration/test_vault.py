import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy


class StateMachine:
    user = strategy("address", exclude=ZERO_ADDRESS)
    deposit_amount = strategy("uint256", min_value=1, max_value=10 ** 27)
    shares_to_withdraw = strategy("uint256", min_value=1, max_value=10 ** 27)
    borrow_amount = strategy("uint256", min_value=1)
    repay_amount = strategy("uint256", min_value=1)
    gain = strategy("uint256", min_value=1, max_value=10 ** 27)
    loss = strategy("uint256", min_value=1)

    def __init__(cls, setup, vault, fundManager, admin, token, uToken, TestStrategy):
        cls.vault = vault
        cls.fundManager = fundManager
        cls.token = token
        cls.uToken = uToken
        cls.admin = admin

    def setup(self):
        self.totalAssets = 0
        self.balanceOfVault = 0
        self.debt = 0

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
            self.balanceOfVault += deposit_amount

    def rule_withdraw_no_loss(self, user, shares_to_withdraw):
        shares = min(shares_to_withdraw, self.uToken.balanceOf(user))

        if shares > 0:
            bal = self.token.balanceOf(self.vault)
            calc = self.vault.calcWithdraw(shares)

            print("withdraw", user, shares, calc)

            self.vault.withdraw(shares, 0, {"from": user})

            self.totalAssets -= calc
            if calc > bal:
                self.balanceOfVault = 0
                self.debt -= calc - bal
            else:
                self.balanceOfVault -= calc

    def rule_withdraw_loss(self, user, shares_to_withdraw, loss):
        shares = min(shares_to_withdraw, self.uToken.balanceOf(user))

        # def snapshot():
        #     return {
        #         "token": {
        #             "vault": self.token.balanceOf(self.vault),
        #             "fundManager": self.token.balanceOf(self.fundManager),
        #         },
        #         "vault": {
        #             "totalAssets": self.vault.totalAssets(),
        #             "balanceOfVault": self.vault.balanceOfVault(),
        #             "debt": self.vault.debt(),
        #         },
        #         "fundManager": {
        #             "totalAssets": self.fundManager.totalAssets(),
        #             "totalDebt": self.fundManager.totalDebt(),
        #         },
        #     }

        if shares > 0:
            bal = self.token.balanceOf(self.vault)
            calc = self.vault.calcWithdraw(shares)

            _loss = min(
                loss,
                self.vault.debt(),
                # loss >= amount to withdraw from fund manager
                max(0, calc - bal),
            )
            if _loss > 0:
                # make sure fund manager can at least withdraw amount >= 1
                _loss -= 1
                self.token.burn(self.fundManager, _loss)

            print("withdraw loss", user, shares, _loss, calc)

            self.vault.withdraw(shares, 0, {"from": user})

            if bal >= calc:
                self.totalAssets -= calc
                self.balanceOfVault -= calc
            else:
                self.totalAssets -= calc
                self.balanceOfVault -= bal
                self.debt -= calc - bal

    def rule_borrow(self, borrow_amount):
        available = self.vault.calcAvailableToInvest()
        borrow = min(borrow_amount, available)

        if borrow > 0:
            print("borrow", borrow)

            self.fundManager.borrowFromVault(borrow, 1, {"from": self.admin})

            self.balanceOfVault -= borrow
            self.debt += borrow

    def rule_repay(self, repay_amount):
        debt = self.vault.debt()
        repay = min(repay_amount, debt, self.token.balanceOf(self.fundManager))

        if repay > 0:
            print("repay", repay)

            self.fundManager.repayVault(repay, 1, {"from": self.admin})

            self.balanceOfVault += repay
            self.debt -= repay

    def rule_report_gain(self, gain):
        print("gain", gain)
        self.token.mint(self.fundManager, gain)

        total = self.fundManager.totalAssets()
        debt = self.vault.debt()
        expected_gain = min(gain, total - debt)

        self.fundManager.reportToVault(0, 2 ** 256 - 1, {"from": self.admin})

        self.totalAssets += expected_gain
        self.debt += expected_gain

    def rule_report_loss(self, loss):
        # can't lose more than debt or token balance of fund manager
        _loss = min(loss, self.vault.debt(), self.token.balanceOf(self.fundManager))

        if _loss > 0:
            print("loss", _loss)

            self.token.burn(self.fundManager, _loss)
            self.fundManager.reportToVault(0, 2 ** 256 - 1, {"from": self.admin})

            self.totalAssets -= _loss
            self.debt -= _loss

    def invariant(self):
        assert self.totalAssets == self.balanceOfVault + self.debt
        assert self.vault.totalAssets() == self.totalAssets
        assert self.vault.balanceOfVault() == self.balanceOfVault
        assert self.vault.debt() == self.debt


def test_stateful(
    setup, vault, fundManager, admin, token, uToken, TestStrategy, state_machine
):
    state_machine(
        StateMachine, setup, vault, fundManager, admin, token, uToken, TestStrategy
    )
