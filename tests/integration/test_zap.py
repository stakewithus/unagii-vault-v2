import brownie


def test_zap(setup, vault, token, uToken, zap, user):
    vault.setWhitelist(zap, True)

    amount = 1000
    token.mint(user, amount)

    token.approve(zap, amount, {"from": user})
    zap.zapIn(amount, {"from": user})

    shares = uToken.balanceOf(user)
    uToken.approve(zap, shares, {"from": user})

    zap.zapOut(shares, {"from": user})

    assert token.balanceOf(user) == amount
