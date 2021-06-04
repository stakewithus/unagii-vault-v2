import brownie
import pytest


def test_skim(vault, token, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.skim({"from": user})

    token.mint(vault, 123)

    diff = token.balanceOf(vault) - vault.balanceOfVault()

    def snapshot():
        return {
            "vault": {"balanceOfVault": vault.balanceOfVault()},
            "token": {
                "admin": token.balanceOf(admin),
                "vault": token.balanceOf(vault),
            },
        }

    before = snapshot()
    vault.skim({"from": admin})
    after = snapshot()

    assert after["token"]["admin"] == before["token"]["admin"] + diff
    assert after["token"]["vault"] == before["token"]["vault"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["balanceOfVault"] == after["token"]["vault"]
