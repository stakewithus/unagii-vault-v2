import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_white_list(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setWhitelist(accounts[0], True, {"from": accounts[1]})

    # admin can call
    vault.setWhitelist(accounts[0], True, {"from": admin})
    assert vault.whitelist(accounts[0])
