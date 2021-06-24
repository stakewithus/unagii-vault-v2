import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_withdraw_not_vault(fundManager, user):
    with brownie.reverts("!vault"):
        fundManager.withdraw(0, {"from": user})


def test_withdraw_zero(fundManager, testVault):
    with brownie.reverts("withdraw = 0"):
        fundManager.withdraw(0, {"from": testVault})


@given(
    withdraw_amount=strategy("uint256", exclude=0),
    mint_amount=strategy("uint256", exclude=0),
    debt=strategy("uint256"),
)
def test_withdraw_amount_lte_balance_in_fund_manager(
    fundManager, token, testVault, withdraw_amount, mint_amount, debt
):
    vault = testVault

    # amount <= balance in fund manager
    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "fundManager": token.balanceOf(fundManager),
            },
            "fundManager": {"totalDebt": fundManager.totalDebt()},
        }

    token.mint(fundManager, mint_amount)

    total = fundManager.totalAssets()
    vault.setDebt(debt)
    loss = 0
    if debt > total:
        loss = debt - total

    amount = min(withdraw_amount, mint_amount)

    before = snapshot()
    tx = fundManager.withdraw(amount, {"from": vault})
    after = snapshot()

    assert tx.events["Withdraw"].values() == [vault, amount, amount, loss]
    assert after["token"]["vault"] == before["token"]["vault"] + amount
    assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
    assert after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"]


N = 5  # max active strategies


@given(
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N),
    debtRatios=strategy(
        "uint256[]", min_value=1, max_value=100, min_length=N, max_length=N
    ),
    borrows=strategy(
        "uint256[]", min_value=1, max_value=2 ** 256 - 1, min_length=N, max_length=N
    ),
    losses=strategy(
        "uint256[]", min_value=1, max_value=2 ** 256 - 1, min_length=N, max_length=N
    ),
    debt=strategy("uint256"),
    withdraw_amount=strategy("uint256", min_value=1),
    mint_amount=strategy("uint256", min_value=1, max_value=2 ** 128),
)
def test_withdraw(
    fundManager,
    token,
    testVault,
    admin,
    TestErc20Strategy,
    k,
    debtRatios,
    borrows,
    losses,
    debt,
    withdraw_amount,
    mint_amount,
):
    vault = testVault
    timeLock = fundManager.timeLock()

    token.mint(fundManager, mint_amount)

    strats = []
    for i in range(k):
        strat = TestErc20Strategy.deploy(fundManager, token, {"from": admin})
        fundManager.approveStrategy(strat, {"from": timeLock})
        fundManager.addStrategyToQueue(
            strat, debtRatios[i], 0, 2 ** 256 - 1, {"from": admin}
        )
        strats.append(strat)

    debts = []
    _withdraw_amount = withdraw_amount  # make sure withdraw amount >= losses
    for i in range(k):
        strat = strats[i]
        borrow = min(fundManager.calcMaxBorrow(strat), borrows[i])
        if borrow > 0:
            fundManager.borrow(borrow, {"from": strat})
            loss = min(losses[i], borrow, _withdraw_amount)
            _withdraw_amount -= loss
            strat.setLoss(loss)
        debts.append(borrow)

    vault.setDebt(debt)

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
    amount = min(withdraw_amount, total)

    before = snapshot()
    fundManager.withdraw(withdraw_amount, {"from": vault})
    after = snapshot()

    if amount <= before["token"]["fundManager"]:
        # amount was only withdrawn from fund manager (not strategies)
        assert (
            after["fundManager"]["totalAssets"]
            == before["fundManager"]["totalAssets"] - amount
        )
        assert after["token"]["fundManager"] == before["token"]["fundManager"] - amount
        assert after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"]
    else:
        # total assets after <= before - amount
        # since there may be losses
        assert (
            after["fundManager"]["totalAssets"]
            <= before["fundManager"]["totalAssets"] - amount
        )
        assert after["token"]["fundManager"] == 0
        amount_from_strats = amount - before["token"]["fundManager"]
        assert (
            after["fundManager"]["totalDebt"]
            <= before["fundManager"]["totalDebt"] - amount_from_strats
        )
