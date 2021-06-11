import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_worker_time_lock(fundManager, user):
    timeLock = fundManager.timeLock()

    tx = fundManager.setWorker(user, {"from": timeLock})
    assert fundManager.worker() == user
    assert tx.events["SetWorker"].values() == [user]


def test_set_worker_admin(fundManager, admin, user):
    fundManager.setWorker(user, {"from": admin})
    assert fundManager.worker() == user


def test_set_worker_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setWorker(user, {"from": user})