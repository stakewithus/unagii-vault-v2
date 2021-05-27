import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_accept_minter(accounts, uToken, minter):
    uToken.setNextMinter(accounts[1], {"from": minter})

    # not next minter
    with brownie.reverts("!next minter"):
        uToken.acceptMinter({"from": accounts[0]})

    uToken.acceptMinter({"from": accounts[1]})
    assert uToken.minter() == accounts[1]
