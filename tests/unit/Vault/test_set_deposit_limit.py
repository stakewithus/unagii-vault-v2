import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_deposit_limit(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setDepositLimit(123, {"from": accounts[1]})

    # admin can call
    vault.setDepositLimit(123, {"from": admin})
    assert vault.depositLimit() == 123
