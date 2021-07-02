import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, ethVault, testEthFundManager):
    if ethVault.fundManager() != testEthFundManager.address:
        timeLock = ethVault.timeLock()
        ethVault.setFundManager(testEthFundManager, {"from": timeLock})


@given(
    gain=strategy("uint256", min_value=0, max_value=1000),
    # delta time to wait
    dt=strategy("uint256", min_value=0, max_value=24 * 3600),
)
def test_calc_locked_profit(chain, ethVault, testEthFundManager, gain, dt, user):
    vault = ethVault
    fundManager = testEthFundManager

    # report
    user.transfer(fundManager, gain)
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
