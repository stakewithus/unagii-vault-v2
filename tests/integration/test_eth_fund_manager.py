import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

# max active strategies
N = 20
# number of active strategies
k = 5


class StateMachine:
    # amount to mint to fund manager
    mint_amount = strategy("uint256", min_value=1, max_value=10)
    # index of active strategy
    i = strategy("uint256", max_value=k - 1)
    borrow_amount = strategy("uint256", min_value=1)
    repay_amount = strategy("uint256", min_value=1, max_value=10)
    gain = strategy("uint256", min_value=1, max_value=10)
    loss = strategy("uint256", min_value=1, max_value=2 ** 128)

    def __init__(cls, setup_eth, ethFundManager, admin, TestStrategyEth, eth_whale):
        fundManager = ethFundManager
        timeLock = fundManager.timeLock()

        cls.fundManager = fundManager
        cls.admin = admin
        cls.strategies = []
        cls.timeLock = timeLock
        cls.eth_whale = eth_whale

        eth_whale.transfer(fundManager, 100)

        for i in range(k):
            strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})
            cls.strategies.append(strat)
            fundManager.approveStrategy(strat, {"from": timeLock})
            fundManager.addStrategyToQueue(strat, 100, 0, 2 ** 256 - 1, {"from": admin})

    def setup(self):
        self.totalAssets = 100
        self.bal = self.totalAssets
        self.totalDebt = 0

    def rule_mint(self, mint_amount):
        total = self.fundManager.totalAssets()
        if total + mint_amount < 2 ** 256:
            self.eth_whale.transfer(self.fundManager, mint_amount)

            self.totalAssets += mint_amount
            self.bal += mint_amount

            print("mint", mint_amount)

    def rule_borrow(self, i, borrow_amount):
        strat = self.strategies[i]
        max_borrow = self.fundManager.calcMaxBorrow(strat)
        if max_borrow > 0:
            self.fundManager.borrow(borrow_amount, {"from": strat})

            _borrow = min(borrow_amount, max_borrow)
            self.totalDebt += _borrow
            self.bal -= _borrow

            print("borrow", _borrow, i)

    def rule_repay(self, i, repay_amount):
        strat = self.strategies[i]
        debt = self.fundManager.getDebt(strat)
        if debt > 0:
            self.fundManager.repay(repay_amount, {"from": strat, "value": repay_amount})

            _repay = min(repay_amount, debt)
            self.totalDebt -= _repay
            self.bal += _repay

            print("repay", _repay, i)

    def rule_report_gain(self, i, gain):
        strat = self.strategies[i]

        self.eth_whale.transfer(strat, gain)
        self.fundManager.report(gain, 0, {"from": strat, "value": gain})

        self.totalAssets += gain
        self.bal += gain

        print("gain", gain, i)

    def rule_report_loss(self, i, loss):
        strat = self.strategies[i]

        bal = strat.balance()
        _loss = min(bal, loss)
        strat.burn(_loss)
        self.fundManager.report(0, _loss, {"from": strat})

        self.totalAssets -= _loss
        self.totalDebt -= _loss

        print("loss", _loss, i)

    def invariant(self):
        # print(self.totalAssets, self.bal, self.totalDebt)

        assert self.totalAssets == self.bal + self.totalDebt
        assert self.fundManager.totalAssets() == self.totalAssets
        assert self.fundManager.totalDebt() == self.totalDebt
        assert self.fundManager.balance() == self.bal


def test_stateful(
    setup_eth, ethFundManager, admin, TestStrategyEth, eth_whale, state_machine
):
    state_machine(
        StateMachine, setup_eth, ethFundManager, admin, TestStrategyEth, eth_whale
    )
