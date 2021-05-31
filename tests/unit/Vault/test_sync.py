import brownie
import pytest


def test_sync(vault, token, admin, user):
    def snapshot():
        return {
            "vault": {"balanceInVault": vault.balanceInVault()},
            "token": {
                "vault": token.balanceOf(vault),
            },
        }

    # not admin
    with brownie.reverts("!admin"):
        vault.sync({"from": user})

    print("FEEE", token.fee())
    # deposit to increase balanceInVault
    token.mint(user, 123)
    token.approve(vault, 123, {"from": user})
    vault.deposit(123, 1, {"from": user})

    # token balance of vault >= balanceInVault
    with brownie.reverts("bal >= vault"):
        vault.sync({"from": admin})

    # force token balance of vault < balanceInVault
    token.burn(vault, 1)

    before = snapshot()
    vault.sync({"from": admin})
    after = snapshot()

    assert after["vault"]["balanceInVault"] == before["token"]["vault"]
    assert after["token"]["vault"] == before["token"]["vault"]
