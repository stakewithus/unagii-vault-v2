import brownie
import pytest


def test_force_update_balance_in_vault(vault, token, admin, user):
    # not admin
    with brownie.reverts("!admin"):
        vault.forceUpdateBalanceInVault({"from": user})

    # deposit to increase balanceInVault
    token.mint(user, 123)
    token.approve(vault, 123, {"from": user})
    vault.deposit(123, 1, {"from": user})

    # token balance of vault >= balanceInVault
    with brownie.reverts("bal >= vault"):
        vault.forceUpdateBalanceInVault({"from": admin})

    # force token balance of vault < balanceInVault
    token.burn(vault, 1)

    def snapshot():
        return {
            "vault": {"balanceInVault": vault.balanceInVault()},
            "token": {
                "vault": token.balanceOf(vault),
            },
        }

    before = snapshot()
    tx = vault.forceUpdateBalanceInVault({"from": admin})
    after = snapshot()

    assert after["vault"]["balanceInVault"] == before["token"]["vault"]
    assert after["token"]["vault"] == before["token"]["vault"]
    assert len(tx.events) == 1
    assert tx.events["ForceUpdateBalanceInVault"].values() == [
        after["vault"]["balanceInVault"]
    ]
