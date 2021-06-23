import brownie
from brownie import ZERO_ADDRESS
import pytest

DELAY = 24 * 3600


def test_vault_set_fund_manager(
    chain, setup, vault, FundManager, timeLock, token, guardian, worker, admin
):
    fundManager = FundManager.deploy(
        token, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.setVault(vault, {"from": admin})

    data = vault.setFundManager.encode_input(fundManager)
    tx = timeLock.queue(vault, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(vault, 0, data, eta, 0, {"from": admin})

    assert vault.fundManager() == fundManager
