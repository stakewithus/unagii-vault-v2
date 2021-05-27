import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_accept_admin(accounts, uToken):
    admin = uToken.admin()
    uToken.setNextAdmin(accounts[1], {"from": admin})

    # not next admin
    with brownie.reverts("!next admin"):
        uToken.acceptAdmin({"from": accounts[0]})

    uToken.acceptAdmin({"from": accounts[1]})
    assert uToken.admin() == accounts[1]
