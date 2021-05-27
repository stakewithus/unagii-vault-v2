import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_pause(accounts, vault, admin, guardian):
    # not admin
    with brownie.reverts("!authorized"):
        vault.setPause(True, {"from": accounts[1]})

    # guadian can pause
    vault.setPause(False, {"from": guardian})
    assert not vault.paused()

    # admin can pause
    vault.setPause(True, {"from": admin})
    assert vault.paused()
