import brownie
import pytest


def test_skim(vault, token, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.skim({"from": user})

    token.mint(vault, 123)

    diff = token.balanceOf(vault) - vault.balanceInVault()

    def snapshot():
        return {
            "vault": {"balanceInVault": vault.balanceInVault()},
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
    assert after["vault"]["balanceInVault"] == before["vault"]["balanceInVault"]
    assert after["vault"]["balanceInVault"] == after["token"]["vault"]
