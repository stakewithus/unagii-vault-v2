import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy
from brownie import StrategyTest


N = 5


class StateMachine:
    i = strategy("uint256", max_value=N - 1)

    def __init__(cls, accounts, vault, token, admin, treasury):
        cls.accounts = accounts
        cls.vault = vault
        cls.timeLock = vault.timeLock()
        cls.admin = admin
        cls.strategies = []
        for i in range(N):
            min_tvl = 100
            max_tvl = 10000
            cls.strategies.append(
                StrategyTest.deploy(
                    token, vault, treasury, min_tvl, max_tvl, {"from": cls.timeLock}
                )
            )

    def setup(self):
        self.approved = {}
        self.active = {}
        self.queue = []

    def rule_approve(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if not strat["approved"]:
            self.vault.approveStrategy(addr, {"from": self.timeLock})
            self.approved[addr] = True

    def rule_revoke(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.vault.revokeStrategy(addr, {"from": self.admin})
            self.approved[addr] = False

    def rule_activate(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and not strat["active"]:
            self.vault.activateStrategy(addr, 1, {"from": self.admin})
            self.active[addr] = True
            self.queue.append(addr)

    def rule_deactivate(self, i):
        addr = self.strategies[i]
        strat = self.vault.strategies(addr)

        if strat["approved"] and strat["active"]:
            self.vault.deactivateStrategy(addr, {"from": self.admin})
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


def test_stateful(vault, token, accounts, admin, treasury, state_machine):
    state_machine(StateMachine, accounts, vault, token, admin, treasury)