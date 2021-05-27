import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_accept_admin(accounts, vault, admin):
    vault.setNextAdmin(accounts[1], {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        vault.acceptAdmin({"from": accounts[0]})

    vault.acceptAdmin({"from": accounts[1]})
    assert vault.admin() == accounts[1]
    assert vault.nextAdmin() == ZERO_ADDRESS
