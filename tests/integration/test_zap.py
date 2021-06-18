import brownie
import pytest


def test_flash(setup, vault, token, uToken, zap, user):
    amount = 1000
    token.mint(user, amount)

    token.approve(zap, amount, {"from": user})
    zap.zapIn(amount, {"from": user})

    shares = uToken.balanceOf(user)
    uToken.approve(zap, shares, {"from": user})

    # protected by block delay
    with brownie.reverts():
        zap.zapOut(shares, {"from": user})

    vault.setWhitelist(zap, True)

    zap.zapOut(shares, {"from": user})

    assert token.balanceOf(user) == amount
