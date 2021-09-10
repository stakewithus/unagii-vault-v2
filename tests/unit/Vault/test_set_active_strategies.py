import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
from brownie import TestStrategy
import pytest

N = 20
# empty strategies
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
    # number of active strategies
    k=strategy("uint256", min_value=0, max_value=N),
    # swap i and j strategy
    i=strategy("uint256", min_value=0, max_value=N),
    j=strategy("uint256", min_value=0, max_value=N),
)
def test_set_active_strategies(vault, token, admin, user, k, i, j):
    timeLock = vault.timeLock()

    # not auth
    with brownie.reverts("!auth"):
        vault.setActiveStrategies(EMPTY, {"from": user})

    # activate strategies
    strats = []
    for i in range(k):
        strat = TestStrategy.deploy(vault, token, {"from": admin})
        vault.approveStrategy(strat, {"from": timeLock})
        vault.activateStrategy(strat, 1, {"from": admin})
        strats.append(strat.address)

    # 0 active strategies
    if k == 0:
        addrs = EMPTY
        vault.setActiveStrategies(addrs, {"from": admin})

        for i in range(len(addrs)):
            assert vault.activeStrategies(i) == ZERO_ADDRESS

    # test number of new strategies > old strategies
    if k > 0 and k < N - 1:
        addrs = merge(EMPTY, strats)
        addrs[k] = addrs[k - 1]

        with brownie.reverts("new != zero address"):
            vault.setActiveStrategies(addrs, {"from": admin})

    # test number of new strategies < old strategies
    if k > 0:
        addrs = merge(EMPTY, strats)
        addrs[k - 1] = ZERO_ADDRESS

        with brownie.reverts("new = zero address"):
            vault.setActiveStrategies(addrs, {"from": admin})

    # test duplicate
    if k >= 2:
        addrs = merge(EMPTY, strats)
        addrs[0] = addrs[1]
        with brownie.reverts("!active"):
            vault.setActiveStrategies(addrs, {"from": admin})

    # update
    if k >= 2:
        addrs = merge(EMPTY, strats)

        _i = min(i, k - 1)
        _j = min(j, k - 1)
        swap(addrs, _i, _j)

        # print("SWAP", _i, _j)
        # print("OLD", strats)
        # print("NEW", addrs)

        vault.setActiveStrategies(addrs, {"from": admin})

        for i in range(len(addrs)):
            assert vault.activeStrategies(i) == addrs[i]
            if addrs[i] != ZERO_ADDRESS:
                assert vault.strategies(addrs[i])["active"]
