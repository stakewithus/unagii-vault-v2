import brownie
from brownie import ZERO_ADDRESS
from brownie.test import strategy


class StateMachine:
    def __init__(cls, setup, vault, fundManager, admin, token, TestStrategy):
        pass

    def setup(self):
        pass

    def rule_pass(self):
        pass

    def invariant(self):
        # TODO: test totalAssets
        # TODO: test debt
        # TODO: test calc locked profit
        # TODO: test free funds
        # TODO: test balance of vault
        # TODO: test deposit
        # TODO: test withdraw
        # TODO: test withdraw from strats
        # TODO: test withdraw shares to burn
        # TODO: test available to invest
        # TODO: test borrow
        # TODO: test repay
        # TODO: test report
        pass


def test_stateful(setup, vault, fundManager, admin, token, TestStrategy, state_machine):
    state_machine(StateMachine, setup, vault, fundManager, admin, token, TestStrategy)