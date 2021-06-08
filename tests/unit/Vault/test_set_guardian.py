import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_admin(vault, admin, user):
    tx = vault.setGuardian(user, {"from": admin})
    assert vault.guardian() == user
    assert len(tx.events) == 1
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_keeper(vault, keeper, user):
    vault.setGuardian(user, {"from": keeper})
    assert vault.guardian() == user


def test_set_guardian_not_auth(vault, user):
    with brownie.reverts("!auth"):
        vault.setGuardian(user, {"from": user})