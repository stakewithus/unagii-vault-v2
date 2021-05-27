import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_next_admin(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setNextAdmin(accounts[1], {"from": accounts[1]})

    # next admin is current admin
    with brownie.reverts("next admin = current"):
        vault.setNextAdmin(admin, {"from": admin})

    vault.setNextAdmin(accounts[1], {"from": admin})
    assert vault.nextAdmin(), accounts[1]
