import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_time_lock(ethVault, user):
    timeLock = ethVault.timeLock()

    tx = ethVault.setGuardian(user, {"from": timeLock})
    assert ethVault.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_admin(ethVault, admin, user):
    ethVault.setGuardian(user, {"from": admin})
    assert ethVault.guardian() == user


def test_set_guardian_not_auth(ethVault, user):
    with brownie.reverts("!auth"):
        ethVault.setGuardian(user, {"from": user})