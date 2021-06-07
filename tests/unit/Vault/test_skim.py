import brownie
import pytest


def test_skim(vault, token, admin, keeper, user):
    # not auth
    with brownie.reverts("!auth"):
        vault.skim({"from": user})

    token.mint(vault, 123)

    diff = token.balanceOf(vault) - vault.balanceOfVault()

    def snapshot():
        return {
            "vault": {"balanceOfVault": vault.balanceOfVault()},
            "token": {
                "admin": token.balanceOf(admin),
                "keeper": token.balanceOf(keeper),
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

    # keeper
    token.mint(vault, 1)

    before = snapshot()
    vault.skim({"from": keeper})
    after = snapshot()

    assert after["token"]["keeper"] == before["token"]["keeper"] + 1