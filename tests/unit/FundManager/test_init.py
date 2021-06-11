import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_init(fundManager, token, admin, guardian, worker):
    assert fundManager.token() == token
    assert fundManager.timeLock() == admin
    assert fundManager.admin() == admin
    assert fundManager.guardian() == guardian
    assert fundManager.worker() == worker