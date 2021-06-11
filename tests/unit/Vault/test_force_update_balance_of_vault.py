import brownie
import pytest


def test_force_update_balance_of_vault(vault, token, admin, user):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.forceUpdateBalanceOfVault({"from": user})

    # deposit to increase balanceOfVault
    token.mint(user, 123)
    token.approve(vault, 123, {"from": user})
    vault.deposit(123, 1, {"from": user})

    # token balance of vault >= balanceOfVault
    with brownie.reverts("bal >= vault"):
        vault.forceUpdateBalanceOfVault({"from": admin})

    # force token balance of vault < balanceOfVault
    token.burn(vault, 1)

    def snapshot():
        return {
            "vault": {"balanceOfVault": vault.balanceOfVault()},
            "token": {
                "vault": token.balanceOf(vault),
            },
        }

    before = snapshot()
    tx = vault.forceUpdateBalanceOfVault({"from": timeLock})
    after = snapshot()

    assert after["vault"]["balanceOfVault"] == before["token"]["vault"]
    assert after["token"]["vault"] == before["token"]["vault"]
    assert len(tx.events) == 1
    assert tx.events["ForceUpdateBalanceOfVault"].values() == [
        after["vault"]["balanceOfVault"]
    ]

    # admin
    # force token balance of vault < balanceOfVault
    token.burn(vault, 1)
    vault.forceUpdateBalanceOfVault({"from": admin})