import brownie
from brownie import ZERO_ADDRESS


def test_withdraw(fundManager, token, admin, keeper, testVault, TestStrategy, user):
    vault = testVault

    # revert if not vault
    with brownie.reverts("!vault"):
        fundManager.withdraw(0, {"from": user})

    # amount <= balance in vault
    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "fundManager": {"totalDebt": fundManager.totalDebt()},
        }

    token.mint(fundManager, 1000)

    amount = 100

    before = snapshot()
    tx = fundManager.withdraw(amount, {"from": vault})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [vault, amount, 0]
    assert after["token"]["vault"] == before["token"]["vault"] + amount
    assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount

    # amount > balance in vault (0 strategies)
    before = snapshot()
    tx = fundManager.withdraw(2 ** 256 - 1, {"from": vault})
    after = snapshot()

    assert (
        after["token"]["vault"]
        == before["token"]["vault"] + before["token"]["fundManager"]
    )
    assert after["token"]["fundManager"] == 0

    # amount > balance in vault (several strategies, 0 loss)
    k = 5
    strats = []
    for i in range(k):
        strat = TestStrategy.deploy(fundManager, token, {"from": admin})
        fundManager.approveStrategy(strat, {"from": admin})
        fundManager.addStrategyToQueue(strat, 1, 0, 100, {"from": admin})
        strats.append(strat)

        token.mint(fundManager, 100)
        token.approve(fundManager, 2 ** 256 - 1, {"from": strat})

        fundManager.borrow(100, {"from": strat})

    before = snapshot()
    tx = fundManager.withdraw(2 ** 256 - 1, {"from": vault})
    after = snapshot()

    assert (
        after["token"]["vault"]
        == before["token"]["vault"]
        + before["token"]["fundManager"]
        + before["fundManager"]["totalDebt"]
    )
    assert after["token"]["fundManager"] == 0
    assert after["fundManager"]["totalDebt"] == 0

    # amount > balance in vault (several strategies, loss > 0)
    token.mint(fundManager, k * 100)
    loss = 0
    borrowed = 0
    for i in range(k):
        strat = strats[i]

        fundManager.borrow(90, {"from": strat})
        borrowed += 90
        strat.setLoss(1)
        loss += 1

    before = snapshot()
    tx = fundManager.withdraw(2 ** 256 - 1, {"from": vault})
    after = snapshot()

    assert (
        after["token"]["vault"]
        == before["token"]["vault"] + before["token"]["fundManager"] + borrowed - loss
    )
    assert after["token"]["fundManager"] == 0
    assert after["fundManager"]["totalDebt"] == 0
