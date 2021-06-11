import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_admin_time_lock(fundManager, user):
    timeLock = fundManager.timeLock()

    tx = fundManager.setAdmin(user, {"from": timeLock})
    assert fundManager.admin() == user
    assert tx.events["SetAdmin"].values() == [user]


def test_set_admin_admin(fundManager, admin, user):
    fundManager.setAdmin(user, {"from": admin})
    assert fundManager.admin() == user


def test_set_admin_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setAdmin(user, {"from": user})