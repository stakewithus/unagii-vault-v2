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