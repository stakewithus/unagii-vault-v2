import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_withdraw_not_vault(fundManager, user):
    print(user, fundManager.vault())
    with brownie.reverts("!vault"):
        fundManager.withdraw(0, {"from": user})


def test_withdraw_zero(fundManager, testVault):
    with brownie.reverts("withdraw = 0"):
        fundManager.withdraw(0, {"from": testVault})


@given(
    withdraw_amount=strategy("uint256", exclude=0),
    mint_amount=strategy("uint256", exclude=0),
)
def test_withdraw_amount_lte_balance_in_vault(
    fundManager, token, testVault, withdraw_amount, mint_amount
):
    vault = testVault

    # amount <= balance in vault
    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "fundManager": {"totalDebt": fundManager.totalDebt()},
        }

    token.mint(fundManager, mint_amount)

    amount = min(withdraw_amount, mint_amount)

    before = snapshot()
    tx = fundManager.withdraw(amount, {"from": vault})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [vault, amount, amount, 0]
    assert after["token"]["vault"] == before["token"]["vault"] + amount
    assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
    assert after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"]


N = 5  # max active strategies


@given(
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N - 1),
    debtRatios=strategy(
        "uint256[]", min_value=1, max_value=100, min_length=N, max_length=N
    ),
    borrows=strategy(
        "uint256[]", min_value=1, max_value=2 ** 256 - 1, min_length=N, max_length=N
    ),
    losses=strategy(
        "uint256[]", min_value=1, max_value=2 ** 256 - 1, min_length=N, max_length=N
    ),
    withdraw_amount=strategy("uint256", min_value=1),
    mint_amount=strategy("uint256", min_value=1, max_value=2 ** 128),
)
def test_withdraw(
    fundManager,
    token,
    testVault,
    admin,
    keeper,
    TestStrategy,
    k,
    debtRatios,
    borrows,
    losses,
    withdraw_amount,
    mint_amount,
):
    vault = testVault

    token.mint(fundManager, mint_amount)

    strats = []
    for i in range(k):
        strat = TestStrategy.deploy(fundManager, token, {"from": admin})
        fundManager.approveStrategy(strat, {"from": admin})
        fundManager.addStrategyToQueue(
            strat, debtRatios[i], 0, 2 ** 256 - 1, {"from": keeper}
        )
        strats.append(strat)

        token.approve(fundManager, 2 ** 256 - 1, {"from": strat})

    debts = []
    for i in range(k):
        strat = strats[i]
        borrow = min(fundManager.calcMaxBorrow(strat), borrows[i])
        if borrow > 0:
            fundManager.borrow(borrow, {"from": strat})
            strat.setLoss(min(losses[i], token.balanceOf(strat)))
        debts.append(borrow)

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "fundManager": {
                "totalAssets": fundManager.totalAssets(),
                "totalDebt": fundManager.totalDebt(),
                "debts": [
                    fundManager.strategies(strat.address)["debt"] for strat in strats
                ],
            },
        }

    total = fundManager.totalAssets()

    before = snapshot()
    tx = fundManager.withdraw(withdraw_amount, {"from": vault})
    after = snapshot()

    amount = min(withdraw_amount, total)
    diff = after["token"]["vault"] - before["token"]["vault"]
    loss = amount - diff

    assert tx.events["Withdraw"].values() == [vault, withdraw_amount, diff, loss]

    if amount <= before["token"]["fundManager"]:
        assert loss == 0
        # amount was only withdrawn from fund manager (not strategies)
        assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
        assert after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"]
        assert (
            after["fundManager"]["totalAssets"]
            == before["fundManager"]["totalAssets"] - amount
        )
    else:
        assert after["token"]["fundManager"] == 0
        amount_from_strats = amount - before["token"]["fundManager"]
        assert (
            after["fundManager"]["totalDebt"]
            == before["fundManager"]["totalDebt"] - amount_from_strats
        )
        assert (
            after["fundManager"]["totalAssets"]
            == before["fundManager"]["totalAssets"] - amount
        )
