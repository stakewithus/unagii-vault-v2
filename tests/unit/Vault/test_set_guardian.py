import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_time_lock(vault, user):
    timeLock = vault.timeLock()

    tx = vault.setGuardian(user, {"from": timeLock})
    assert vault.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_admin(vault, admin, user):
    vault.setGuardian(user, {"from": admin})
    assert vault.guardian() == user


def test_set_guardian_not_auth(vault, user):
    with brownie.reverts("!auth"):
        vault.setGuardian(user, {"from": user})