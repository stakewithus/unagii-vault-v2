import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_keeper(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setKeeper(accounts[1], {"from": accounts[1]})

    # new keeper is current keeper
    with brownie.reverts("new keeper = current"):
        vault.setKeeper(vault.keeper(), {"from": admin})

    vault.setKeeper(accounts[0], {"from": admin})
    assert vault.keeper(), accounts[0]
