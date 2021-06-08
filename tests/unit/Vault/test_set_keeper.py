import brownie
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_set_keeper_admin(vault, admin, user):
    tx = vault.setKeeper(user, {"from": admin})
    assert vault.keeper() == user
    assert len(tx.events) == 1
    assert tx.events["SetKeeper"].values() == [user]


def test_set_keeper_keeper(vault, keeper, user):
    vault.setKeeper(user, {"from": keeper})
    assert vault.keeper() == user


def test_set_keeper_not_auth(vault, user):
    with brownie.reverts("!auth"):
        vault.setKeeper(user, {"from": user})