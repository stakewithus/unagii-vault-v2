import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, testFundManager):
    if vault.fundManager() != testFundManager.address:
        timeLock = vault.timeLock()
        vault.setFundManager(testFundManager, {"from": timeLock})


@given(
    gain=strategy("uint256", min_value=0, max_value=2 ** 128),
    # delta time to wait
    dt=strategy("uint256", min_value=0, max_value=24 * 3600),
)
def test_calc_locked_profit(chain, vault, token, testFundManager, gain, dt):
    fundManager = testFundManager

    # report
    token.mint(fundManager, gain)
    vault.report(gain, 0, {"from": fundManager})

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
