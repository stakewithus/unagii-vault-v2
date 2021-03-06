import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
from brownie import TestStrategyEth
import pytest

N = 20
# empty queue
EMPTY = [ZERO_ADDRESS for i in range(N)]

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation):
    pass


# overwrite elements from left to right
def merge(xs, ys):
    zs = [xs[i] for i in range(len(xs))]
    for i in range(len(ys)):
        if i < len(xs):
            zs[i] = ys[i]
        else:
            zs.append(ys[i])
    return zs


def swap(arr, i, j):
    tmp = arr[i]
    arr[i] = arr[j]
    arr[j] = tmp


@given(
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N),
)
def test_set_queue(ethFundManager, admin, user, k):
    fundManager = ethFundManager
    timeLock = fundManager.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        fundManager.setQueue(EMPTY, {"from": user})

    # activate strategies
    strats = []
    for i in range(k):
        strat = TestStrategyEth.deploy(fundManager, ETH, {"from": admin})
        fundManager.approveStrategy(strat, {"from": timeLock})
        fundManager.addStrategyToQueue(strat, 1, 0, 0, {"from": admin})
        strats.append(strat.address)

    # 0 active strategies
    if k == 0:
        queue = merge(EMPTY, [])
        fundManager.setQueue(queue, {"from": admin})

        for i in range(len(queue)):
            assert fundManager.queue(i) == ZERO_ADDRESS

    # check no gaps (replace element at k - 2 with 0 address)
    if k > 2:
        queue = merge(EMPTY, strats)
        queue[k - 2] = ZERO_ADDRESS

        with brownie.reverts("gap"):
            fundManager.setQueue(queue, {"from": admin})

    # check old and new queue have same non zero strategy count
    if k > 0 and k < N - 1:
        queue = merge(EMPTY, strats)
        # count of non zero strategies in new queue > old queue
        queue[k] = queue[k - 1]

        with brownie.reverts("new != 0"):
            fundManager.setQueue(queue, {"from": admin})

    if k > 0:
        queue = merge(EMPTY, strats)
        # count of non zero strategies in new queue < old queue
        queue[k - 1] = ZERO_ADDRESS

        with brownie.reverts("new = 0"):
            fundManager.setQueue(queue, {"from": admin})

    # check duplicate (copy element at 2 to 1)
    if k > 2:
        queue = merge(EMPTY, strats)
        queue[1] = queue[2]
        with brownie.reverts("!active"):
            fundManager.setQueue(queue, {"from": admin})

    # update
    if k > 4:
        queue = merge(EMPTY, strats)
        swap(queue, 4, 1)
        swap(queue, 2, 3)
        fundManager.setQueue(queue, {"from": admin})

        for i in range(len(queue)):
            assert fundManager.queue(i) == queue[i]
            if queue[i] != ZERO_ADDRESS:
                assert fundManager.strategies(queue[i])["active"]
