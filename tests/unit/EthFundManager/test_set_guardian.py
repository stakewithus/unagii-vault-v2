import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_guardian_time_lock(ethFundManager, user):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    tx = fundManager.setGuardian(user, {"from": timeLock})
    assert fundManager.guardian() == user
    assert tx.events["SetGuardian"].values() == [user]


def test_set_guardian_admin(ethFundManager, admin, user):
    ethFundManager.setGuardian(user, {"from": admin})
    assert ethFundManager.guardian() == user


def test_set_guardian_not_auth(ethFundManager, user):
    with brownie.reverts("!auth"):
        ethFundManager.setGuardian(user, {"from": user})