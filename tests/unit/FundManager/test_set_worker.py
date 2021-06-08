import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_worker_admin(fundManager, admin, user):
    tx = fundManager.setWorker(user, {"from": admin})
    assert fundManager.worker() == user
    assert len(tx.events) == 1
    assert tx.events["SetWorker"].values() == [user]


def test_set_worker_keeper(fundManager, keeper, user):
    fundManager.setWorker(user, {"from": keeper})
    assert fundManager.worker() == user


def test_set_worker_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setWorker(user, {"from": user})