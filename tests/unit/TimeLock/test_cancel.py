import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_queue(timeLock, txTest, admin):
    value = 1
    data = "0x1212"
    delay = 24 * 3600
    nonce = 0

    tx = timeLock.queue(txTest, value, data, delay, nonce, {"from": admin})

    eta = tx.timestamp + delay
    txHash = timeLock.getTxHash(txTest, value, data, eta, nonce)

    tx = timeLock.cancel(txTest, value, data, eta, nonce, {"from": admin})

    assert not timeLock.queued(txHash)
    assert len(tx.events) == 1
    assert tx.events["Log"].values() == [txHash, txTest, 1, data, eta, nonce, 2]


def test_cancel_not_admin(timeLock, user):
    with brownie.reverts("!admin"):
        timeLock.cancel(ZERO_ADDRESS, 0, "", 0, 0, {"from": user})


def test_cancel_not_queued(timeLock, admin):
    with brownie.reverts("!queued"):
        timeLock.cancel(ZERO_ADDRESS, 0, "", 0, 0, {"from": admin})