import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_locked_profit_degradation(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setLockedProfitDegradation(123, {"from": accounts[1]})

    # over max
    with brownie.reverts("degradation > max"):
        vault.setLockedProfitDegradation(10 ** 18 + 1, {"from": admin})

    # admin can call
    vault.setLockedProfitDegradation(123, {"from": admin})
    assert vault.lockedProfitDegradation() == 123
