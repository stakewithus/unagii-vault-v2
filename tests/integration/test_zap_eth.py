import brownie


def test_zap(setup_eth, ethVault, uEth, zapEth, user):
    vault = ethVault
    uToken = uEth
    zap = zapEth

    vault.setWhitelist(zap, True)

    amount = 1000

    zap.zapIn({"from": user, "value": amount})

    shares = uToken.balanceOf(user)
    uToken.approve(zap, shares, {"from": user})

    bal_before = user.balance()
    zap.zapOut(shares, {"from": user})
    bal_after = user.balance()

    diff = bal_after - bal_before
    tx_fee = 0
    assert diff == amount - tx_fee
