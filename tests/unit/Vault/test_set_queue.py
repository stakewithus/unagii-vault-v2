import brownie
from brownie.test import given, strategy
from brownie import TestStrategy
import pytest

N = 20
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
# empty queue
EMPTY = [ZERO_ADDRESS for i in range(N)]


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
    k=strategy("uint256", min_value=0, max_value=N - 1),
)
def test_set_queue(vault, token, admin, user, timeLock, k):
    # not admin
    with brownie.reverts("!admin"):
        vault.setQueue(EMPTY, {"from": user})

    # activate strategies
    strats = []
    for i in range(k):
        strat = TestStrategy.deploy(vault, token, {"from": admin})
        vault.approveStrategy(strat.address, 0, 0, 0, {"from": timeLock})
        vault.addStrategyToQueue(strat.address, 0, {"from": admin})
        strats.append(strat.address)

    # 0 active strategies
    if k == 0:
        queue = merge(EMPTY, [])
        vault.setQueue(queue, {"from": admin})

        for i in range(len(queue)):
            assert vault.queue(i) == ZERO_ADDRESS

    # check no gaps (replace element at k - 2 with 0 address)
    if k > 2:
        queue = merge(EMPTY, strats)
        queue[k - 2] = ZERO_ADDRESS

        with brownie.reverts("gap"):
            vault.setQueue(queue, {"from": admin})

    # check old and new queue have same non zero strategy count
    if k > 0:
        queue = merge(EMPTY, strats)
        # count of non zero strategies in new queue > old queue
        queue[k] = queue[k - 1]

        with brownie.reverts("new != 0"):
            vault.setQueue(queue, {"from": admin})

        queue = merge(EMPTY, strats)
        # count of non zero strategies in new queue < old queue
        queue[k - 1] = ZERO_ADDRESS

        with brownie.reverts("new = 0"):
            vault.setQueue(queue, {"from": admin})

    # check duplicate (copy element at 2 to 1)
    if k > 2:
        queue = merge(EMPTY, strats)
        queue[1] = queue[2]
        with brownie.reverts("!active"):
            vault.setQueue(queue, {"from": admin})

    # update
    if k > 4:
        queue = merge(EMPTY, strats)
        swap(queue, 4, 1)
        swap(queue, 2, 3)
        vault.setQueue(queue, {"from": admin})

        for i in range(len(queue)):
            assert vault.queue(i) == queue[i]
            if queue[i] != ZERO_ADDRESS:
                assert vault.strategies(queue[i])["active"]