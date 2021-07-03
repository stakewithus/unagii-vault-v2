import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy

# max queue
N = 20

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


@given(
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N),
    # random numbers for debt ratios
    rands=strategy("uint256[]", min_value=0, max_value=100, min_length=N, max_length=N),
)
def test_set_debt_ratios(ethFundManager, admin, TestStrategyEth, user, k, rands):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    # not authorized
    with brownie.reverts("!auth"):
        debtRatios = [0 for i in range(N)]
        fundManager.setDebtRatios(debtRatios, {"from": user})

    # debt ratios > active strategies
    with brownie.reverts("debt ratio != 0"):
        debtRatios = [0 for i in range(N)]
        debtRatios[1] = 1
        fundManager.setDebtRatios(debtRatios, {"from": admin})

    strats = []
    for i in range(k):
        strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})
        fundManager.approveStrategy(strat, {"from": timeLock})
        fundManager.addStrategyToQueue(strat, 1, 0, 0, {"from": admin})
        strats.append(strat.address)

    # total debt ratio > max
    if k > 0:
        with brownie.reverts("total > max"):
            debtRatios = [0 for i in range(N)]
            debtRatios[0] = 10001
            fundManager.setDebtRatios(debtRatios, {"from": admin})

    debtRatios = [rands[i] if i < k else 0 for i in range(N)]
    totalDebtRatio = sum(debtRatios)

    tx = fundManager.setDebtRatios(debtRatios, {"from": admin})

    assert fundManager.totalDebtRatio() == totalDebtRatio
    assert tx.events["SetDebtRatios"].values() == [debtRatios]

    for i in range(N):
        addr = fundManager.queue(i)
        assert fundManager.strategies(addr)["debtRatio"] == debtRatios[i]
