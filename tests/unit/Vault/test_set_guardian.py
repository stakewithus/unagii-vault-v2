import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_guardian(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setGuardian(accounts[1], {"from": accounts[1]})

    # new guardian is current guardian
    with brownie.reverts("new guardian = current"):
        vault.setGuardian(vault.guardian(), {"from": admin})

    vault.setGuardian(accounts[0], {"from": admin})
    assert vault.guardian(), accounts[0]
