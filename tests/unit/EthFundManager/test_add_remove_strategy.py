import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy
from brownie import TestStrategyEth


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
N = 5


class StateMachine:
    i = strategy("uint256", max_value=N - 1)

    def __init__(cls, accounts, ethFundManager, admin):
        cls.accounts = accounts
        cls.fundManager = ethFundManager
        cls.timeLock = ethFundManager.timeLock()
        cls.admin = admin
        cls.strategies = []
        for i in range(N):
            cls.strategies.append(
                TestStrategyEth.deploy(ethFundManager, ETH, {"from": cls.timeLock})
            )

    def setup(self):
        self.approved = {}
        self.active = {}
        self.queue = []

    def rule_approve(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if not strat["approved"]:
            self.fundManager.approveStrategy(addr, {"from": self.timeLock})
            self.approved[addr] = True

    def rule_revoke(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.fundManager.revokeStrategy(addr, {"from": self.admin})
            self.approved[addr] = False

    def rule_add(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.fundManager.addStrategyToQueue(addr, 1, 2, 3, {"from": self.admin})
            self.active[addr] = True
            self.queue.append(addr)

    def rule_remove(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and strat["active"]:
            self.fundManager.removeStrategyFromQueue(addr, {"from": self.admin})
            self.active[addr] = False
            self.queue.remove(addr)

    def invariant(self):
        for i in range(N):
            addr = self.strategies[i]
            strat = self.fundManager.strategies(addr)
            assert strat["approved"] == self.approved.get(addr, False)
            assert strat["active"] == self.active.get(addr, False)
        for i in range(N):
            if i < len(self.queue):
                assert self.fundManager.queue(i) == self.queue[i]
            else:
                assert self.fundManager.queue(i) == ZERO_ADDRESS

        # print("queue", self.queue)
        # print("approved", self.approved)
        # print("active", self.active)


def test_stateful(ethFundManager, accounts, admin, state_machine):
    state_machine(StateMachine, accounts, ethFundManager, admin)