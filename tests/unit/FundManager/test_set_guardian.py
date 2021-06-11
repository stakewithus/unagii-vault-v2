import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_time_lock(fundManager, user):
    timeLock = fundManager.timeLock()

    tx = fundManager.setGuardian(user, {"from": timeLock})
    assert fundManager.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_admin(fundManager, admin, user):
    fundManager.setGuardian(user, {"from": admin})
    assert fundManager.guardian() == user


def test_set_guardian_not_auth(fundManager, user):
    with brownie.reverts("!auth"):
        fundManager.setGuardian(user, {"from": user})