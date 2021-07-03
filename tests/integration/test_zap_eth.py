import brownie
import pytest


def test_zap_eth(setup_eth, ethVault, uEth, zapEth, user):
    zap = zapEth
    uToken = uEth
    vault = ethVault

    amount = 1000

    zap.zapIn(amount, {"from": user, "value": amount})

    shares = uToken.balanceOf(user)
    uToken.approve(zap, shares, {"from": user})

    # protected by block delay
    with brownie.reverts():
        zap.zapOut(shares, {"from": user})

    vault.setWhitelist(zap, True)

    zap.zapOut(shares, {"from": user})
