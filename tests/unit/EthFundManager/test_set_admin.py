import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_admin_time_lock(ethFundManager, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    tx = fundManager.setAdmin(user, {"from": timeLock})
    assert fundManager.admin() == user
    assert tx.events["SetAdmin"].values() == [user]


def test_set_admin_admin(ethFundManager, admin, user):
    ethFundManager.setAdmin(user, {"from": admin})
    assert ethFundManager.admin() == user


def test_set_admin_not_auth(ethFundManager, user):
    with brownie.reverts("!auth"):
        ethFundManager.setAdmin(user, {"from": user})