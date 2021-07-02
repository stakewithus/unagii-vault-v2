import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_admin_time_lock(ethVault, user):
    timeLock = ethVault.timeLock()

    tx = ethVault.setAdmin(user, {"from": timeLock})
    assert ethVault.admin() == user
    assert tx.events["SetAdmin"].values() == [user]


def test_set_admin_admin(ethVault, admin, user):
    ethVault.setAdmin(user, {"from": admin})
    assert ethVault.admin() == user


def test_set_admin_not_auth(ethVault, user):
    with brownie.reverts("!auth"):
        ethVault.setAdmin(user, {"from": user})