import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_admin(fundManager, admin, user):
    tx = fundManager.setGuardian(user, {"from": admin})
    assert fundManager.guardian() == user
    assert len(tx.events) == 1
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_keeper(fundManager, keeper, user):
    fundManager.setGuardian(user, {"from": keeper})
    assert fundManager.guardian() == user


def test_set_guardian_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setGuardian(user, {"from": user})