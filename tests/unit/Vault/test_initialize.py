import brownie
import pytest


@pytest.fixture
def vault(Vault, token, uToken, admin, timeLock, guardian, keeper):
    yield Vault.deploy(token, uToken, timeLock, guardian, keeper, {"from": admin})


def test_initialize(vault, uToken, minter, admin, user):
    assert not vault.initialized()

    # cannot initialize if not admin
    with brownie.reverts("!admin"):
        vault.initialize({"from": user})

    uToken.setNextMinter(vault, {"from": minter})
    vault.initialize()

    assert vault.initialized({"from": admin})
    assert uToken.minter() == vault

    # cannot initialize more than once
    with brownie.reverts("initialized"):
        vault.initialize()
