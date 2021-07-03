import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


def test_withdraw_not_vault(ethFundManager, user):
    with brownie.reverts("!vault"):
        ethFundManager.withdraw(0, {"from": user})


def test_withdraw_zero(ethFundManager, testEthVault):
    with brownie.reverts("withdraw = 0"):
        ethFundManager.withdraw(0, {"from": testEthVault})


@given(
    withdraw_amount=strategy("uint256", exclude=0),
    mint_amount=strategy("uint256", min_value=1, max_value=1000),
    debt=strategy("uint256"),
)
def test_withdraw_amount_lte_balance_in_fund_manager(
    ethFundManager, testEthVault, withdraw_amount, mint_amount, debt, user
):
    fundManager = ethFundManager
    vault = testEthVault

    # amount <= balance in fund manager
    def snapshot():
        return {
            "eth": {"vault": vault.balance(), "fundManager": fundManager.balance()},
            "fundManager": {"totalDebt": fundManager.totalDebt()},
        }

    user.transfer(fundManager, mint_amount)

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
    assert after["eth"]["vault"] == before["eth"]["vault"] + amount
    assert after["eth"]["fundManager"] == before["eth"]["fundManager"] - amount
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
    mint_amount=strategy("uint256", min_value=1, max_value=1000),
)
def test_withdraw(
    ethFundManager,
    testEthVault,
    admin,
    TestStrategyEth,
    k,
    debtRatios,
    borrows,
    losses,
    debt,
    withdraw_amount,
    mint_amount,
    user,
):
    fundManager = ethFundManager
    vault = testEthVault
    timeLock = fundManager.timeLock()

    user.transfer(fundManager, mint_amount)

    strats = []
    for i in range(k):
        strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})
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
            "eth": {
                "vault": vault.balance(),
                "fundManager": fundManager.balance(),
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

    if amount <= before["eth"]["fundManager"]:
        # amount was only withdrawn from fund manager (not strategies)
        assert (
            after["fundManager"]["totalAssets"]
            == before["fundManager"]["totalAssets"] - amount
        )
        assert after["eth"]["fundManager"] == before["eth"]["fundManager"] - amount
        assert after["fundManager"]["totalDebt"] == before["fundManager"]["totalDebt"]
    else:
        # total assets after <= before - amount
        # since there may be losses
        assert (
            after["fundManager"]["totalAssets"]
            <= before["fundManager"]["totalAssets"] - amount
        )
        assert after["eth"]["fundManager"] == 0
        amount_from_strats = amount - before["eth"]["fundManager"]
        assert (
            after["fundManager"]["totalDebt"]
            <= before["fundManager"]["totalDebt"] - amount_from_strats
        )
