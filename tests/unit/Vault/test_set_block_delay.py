import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_block_delay(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setBlockDelay(123, {"from": accounts[1]})

    # delay = 0
    with brownie.reverts("delay = 0"):
        vault.setBlockDelay(0, {"from": admin})

    # admin can call
    vault.setBlockDelay(123, {"from": admin})
    assert vault.blockDelay() == 123
