import brownie
from brownie.convert.datatypes import _address_compare
from brownie.test import strategy
from brownie import TestStrategy


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
N = 3


class StateMachine:
    i = strategy("uint256", max_value=N - 1)

    def __init__(cls, accounts, vault, admin, timeLock):
        cls.accounts = accounts
        cls.vault = vault
        cls.admin = admin
        cls.timeLock = timeLock
        cls.strategies = []
        for i in range(N):
            cls.strategies.append(
                TestStrategy.deploy(vault, vault.token(), {"from": admin})
            )

    def setup(self):
        self.approved = {}
        self.active = {}
        self.queue = []

    def rule_approve(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if not strat["approved"]:
            self.vault.approveStrategy(addr, 0, 0, 0, {"from": self.timeLock})
            self.approved[addr] = True

    def rule_revoke(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.vault.revokeStrategy(addr, {"from": self.admin})
            self.approved[addr] = False

    def rule_add(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.vault.addStrategyToQueue(addr, 0, {"from": self.admin})
            self.active[addr] = True
            self.queue.append(addr)

    def rule_remove(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and strat["active"]:
            self.vault.removeStrategyFromQueue(addr, {"from": self.admin})
            self.active[addr] = False
            self.queue.remove(addr)

    def invariant(self):
        for i in range(N):
            addr = self.strategies[i]
            strat = self.vault.strategies(addr)
            assert strat["approved"] == self.approved.get(addr, False)
            assert strat["active"] == self.active.get(addr, False)
        for i in range(N):
            if i < len(self.queue):
                assert self.vault.queue(i) == self.queue[i]
            else:
                assert self.vault.queue(i) == ZERO_ADDRESS

        # print("queue", self.queue)
        # print("approved", self.approved)
        # print("active", self.active)


def test_stateful(vault, accounts, admin, timeLock, state_machine):
    state_machine(StateMachine, accounts, vault, admin, timeLock)