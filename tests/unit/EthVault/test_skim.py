import brownie
import pytest


def test_skim(ethVault, admin, user):
    vault = ethVault
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.skim({"from": user})

    user.transfer(vault, 123)

    diff = vault.balance() - vault.balanceOfVault()

    def snapshot():
        return {
            "vault": {"balanceOfVault": vault.balanceOfVault()},
            "eth": {
                "timeLock": timeLock.balance(),
                "admin": admin.balance(),
                "vault": vault.balance(),
            },
        }

    before = snapshot()
    vault.skim({"from": admin})
    after = snapshot()

    assert after["eth"]["admin"] == before["eth"]["admin"] + diff
    assert after["eth"]["vault"] == before["eth"]["vault"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["balanceOfVault"] == after["eth"]["vault"]
