import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_time_lock(accounts, vault, timeLock):
    # not time lock
    with brownie.reverts("!time lock"):
        vault.setTimeLock(accounts[0], {"from": accounts[0]})

    # new time lock is current time lock
    with brownie.reverts("new time lock = current"):
        vault.setTimeLock(timeLock, {"from": timeLock})

    vault.setTimeLock(accounts[0], {"from": timeLock})
    assert vault.timeLock(), accounts[0]
