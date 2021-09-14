import brownie
from brownie import ZERO_ADDRESS, TestStrategyEth
from brownie.test import given, strategy

# max active strategies
N = 20


@given(
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N),
    # random numbers for debt ratios
    rands=strategy("uint256[]", min_value=0, max_value=100, min_length=N, max_length=N),
)
def test_set_debt_ratios(ethVault, admin, user, k, rands):
    vault = ethVault
    timeLock = vault.timeLock()

    # not authorized
    with brownie.reverts("!auth"):
        debtRatios = [0 for i in range(N)]
        vault.setDebtRatios(debtRatios, {"from": user})

    strats = []
    for i in range(k):
        strat = TestStrategyEth.deploy(vault, {"from": admin})
        vault.approveStrategy(strat, {"from": timeLock})
        vault.activateStrategy(strat, 1, {"from": admin})
        strats.append(strat.address)

    # test total debt ratio > max
    if k > 0:
        with brownie.reverts("total > max"):
            debtRatios = [0 for i in range(N)]
            debtRatios[0] = 10001
            vault.setDebtRatios(debtRatios, {"from": admin})

    debtRatios = [rands[i] if i < k else 0 for i in range(N)]
    totalDebtRatio = sum(debtRatios)

    tx = vault.setDebtRatios(debtRatios, {"from": admin})

    assert vault.totalDebtRatio() == totalDebtRatio
    assert tx.events["SetDebtRatios"].values() == [debtRatios]

    for i in range(N):
        addr = vault.activeStrategies(i)
        assert vault.strategies(addr)["debtRatio"] == debtRatios[i]
