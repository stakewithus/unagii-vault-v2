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
        # test totalAssets
        # test debt
        # test calc locked profit
        # test free funds
        # test balance of vault
        # test deposit
        # test withdraw
        # test withdraw from strats
        # test withdraw shares to burn
        # test available to invest
        # test borrow
        # test repay
        # test report
        pass


def test_stateful(setup, vault, fundManager, admin, token, TestStrategy, state_machine):
    state_machine(StateMachine, setup, vault, fundManager, admin, token, TestStrategy)