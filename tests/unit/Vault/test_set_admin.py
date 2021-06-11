import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_admin_time_lock(vault, user):
    timeLock = vault.timeLock()

    tx = vault.setAdmin(user, {"from": timeLock})
    assert vault.admin() == user
    assert tx.events["SetAdmin"].values() == [user]


def test_set_admin_admin(vault, admin, user):
    vault.setAdmin(user, {"from": admin})
    assert vault.admin() == user


def test_set_admin_not_auth(vault, user):
    with brownie.reverts("!auth"):
        vault.setAdmin(user, {"from": user})