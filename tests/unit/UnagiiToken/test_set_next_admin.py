import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_next_admin(accounts, uToken):
    admin = uToken.admin()

    # not admin
    with brownie.reverts("!admin"):
        uToken.setNextAdmin(accounts[1], {"from": accounts[1]})

    # next admin is current admin
    with brownie.reverts("next admin = current"):
        uToken.setNextAdmin(uToken.admin(), {"from": admin})

    uToken.setNextAdmin(accounts[1], {"from": admin})
    assert uToken.nextAdmin(), accounts[1]
