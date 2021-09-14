from brownie import ZERO_ADDRESS
from brownie.test import given, strategy


@given(
    gain=strategy("uint256", min_value=0, max_value=1000),
    # delta time to wait
    dt=strategy("uint256", min_value=0, max_value=24 * 3600),
)
def test_calc_locked_profit(chain, ethVault, admin, testStrategyEth, gain, dt):
    vault = ethVault
    strategy = testStrategyEth
    timeLock = vault.timeLock()

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 1, {"from": admin})

    # sync
    admin.transfer(strategy, gain)
    vault.sync(strategy, 0, 2 ** 256 - 1, {"from": admin})

    chain.mine(timestamp=chain.time() + dt)

    MAX_RATE = 10 ** 18
    rate = vault.lockedProfitDegradation()
    ratio = dt * rate
    locked = vault.lockedProfit()
    calc = vault.calcLockedProfit()

    # print(ratio, locked, calc)

    assert calc <= locked

    if ratio >= MAX_RATE:
        assert calc == 0
