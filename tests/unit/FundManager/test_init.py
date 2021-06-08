import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_init(fundManager, token, admin, guardian, keeper, worker):
    assert fundManager.token() == token
    assert fundManager.admin() == admin
    assert fundManager.guardian() == guardian
    assert fundManager.keeper() == keeper
    assert fundManager.worker() == worker