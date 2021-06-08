import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_keeper_admin(fundManager, admin, user):
    tx = fundManager.setKeeper(user, {"from": admin})
    assert fundManager.keeper() == user
    assert len(tx.events) == 1
    assert tx.events["SetKeeper"].values() == [user]


def test_set_keeper_keeper(fundManager, keeper, user):
    fundManager.setKeeper(user, {"from": keeper})
    assert fundManager.keeper() == user


def test_set_keeper_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setKeeper(user, {"from": user})