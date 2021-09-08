from brownie import ZERO_ADDRESS
from brownie.test import given, strategy


def test_calc_min_reserve(chain, vault, token, admin, testStrategy):
    strategy = testStrategy
    timeLock = vault.timeLock()

    token.mint(vault, 123456)
    free = vault.calcFreeFunds()

    # min reserve = 100 %
    vault.setMinReserve(10000, {"from": admin})
    assert vault.calcMinReserve() == free

    # min reserve = 5%
    vault.setMinReserve(500, {"from": admin})
    assert vault.calcMinReserve() == 0.05 * free

    # min reserve = 0%
    vault.setMinReserve(0, {"from": admin})
    assert vault.calcMinReserve() == 0