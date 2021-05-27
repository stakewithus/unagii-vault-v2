import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_pause(accounts, vault, admin, guardian):
    # not admin
    with brownie.reverts("!authorized"):
        vault.setPause(True, {"from": accounts[1]})

    # new keeper is current keeper
    with brownie.reverts("paused = current"):
        vault.setPause(vault.paused(), {"from": admin})

    # guadian can pause
    vault.setPause(False, {"from": guardian})
    assert not vault.paused()

    # admin can pause
    vault.setPause(True, {"from": admin})
    assert vault.paused()
