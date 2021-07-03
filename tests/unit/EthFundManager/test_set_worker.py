import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_worker_time_lock(ethFundManager, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    tx = fundManager.setWorker(user, {"from": timeLock})
    assert fundManager.worker() == user
    assert tx.events["SetWorker"].values() == [user]


def test_set_worker_admin(ethFundManager, admin, user):
    ethFundManager.setWorker(user, {"from": admin})
    assert ethFundManager.worker() == user


def test_set_worker_not_auth(ethFundManager, user):
    with brownie.reverts("!auth"):
        ethFundManager.setWorker(user, {"from": user})