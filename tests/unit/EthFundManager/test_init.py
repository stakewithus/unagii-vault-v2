import brownie
from brownie import ZERO_ADDRESS
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_init_no_old_fund_manager(ethFundManager, admin, guardian, worker):
    assert ethFundManager.token() == ETH
    assert ethFundManager.timeLock() == admin
    assert ethFundManager.admin() == admin
    assert ethFundManager.guardian() == guardian
    assert ethFundManager.worker() == worker
    assert ethFundManager.oldFundManager() == ZERO_ADDRESS


def test_init_with_old_fund_manager(EthFundManager, admin, guardian, worker):
    oldFundManager = EthFundManager.deploy(
        guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager = EthFundManager.deploy(
        guardian, worker, oldFundManager, {"from": admin}
    )

    assert fundManager.oldFundManager() == oldFundManager