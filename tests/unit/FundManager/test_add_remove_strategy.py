import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy
from brownie import TestStrategy


N = 5


class StateMachine:
    i = strategy("uint256", max_value=N - 1)

    def __init__(cls, accounts, fundManager, admin, keeper):
        cls.accounts = accounts
        cls.fundManager = fundManager
        cls.admin = admin
        cls.keeper = keeper
        cls.strategies = []
        for i in range(N):
            cls.strategies.append(
                TestStrategy.deploy(fundManager, fundManager.token(), {"from": admin})
            )

    def setup(self):
        self.approved = {}
        self.active = {}
        self.queue = []

    def rule_approve(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if not strat["approved"]:
            self.fundManager.approveStrategy(addr, {"from": self.admin})
            self.approved[addr] = True

    def rule_revoke(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.fundManager.revokeStrategy(addr, {"from": self.keeper})
            self.approved[addr] = False

    def rule_add(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.fundManager.addStrategyToQueue(addr, 1, {"from": self.keeper})
            self.active[addr] = True
            self.queue.append(addr)

    def rule_remove(self, i):
        addr = self.strategies[i]
        strat = self.fundManager.strategies(addr)

        if strat["approved"] and strat["active"]:
            self.fundManager.removeStrategyFromQueue(addr, {"from": self.keeper})
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


def test_stateful(fundManager, accounts, admin, keeper, state_machine):
    state_machine(StateMachine, accounts, fundManager, admin, keeper)