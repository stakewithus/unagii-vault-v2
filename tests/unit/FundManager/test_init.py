import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_init_no_old_fund_manager(fundManager, token, admin, guardian, worker):
    assert fundManager.token() == token
    assert fundManager.timeLock() == admin
    assert fundManager.admin() == admin
    assert fundManager.guardian() == guardian
    assert fundManager.worker() == worker
    assert fundManager.oldFundManager() == ZERO_ADDRESS


def test_init_with_old_fund_manager(FundManager, token, admin, guardian, worker):
    oldFundManager = FundManager.deploy(
        ZERO_ADDRESS, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )

    with brownie.reverts("old fund manager token != token"):
        FundManager.deploy(token, guardian, worker, oldFundManager, {"from": admin})

    oldFundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager = FundManager.deploy(
        token, guardian, worker, oldFundManager, {"from": admin}
    )

    assert fundManager.oldFundManager() == oldFundManager