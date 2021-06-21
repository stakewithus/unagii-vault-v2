import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_batch_queue(timeLock, txTest, admin):
    targets = [txTest, txTest]
    values = [1, 2]
    data = ["0x1212", "0x2121"]
    delays = [24 * 3600, 25 * 3600]
    nonces = [0, 1]

    tx = timeLock.batchQueue(targets, values, data, delays, nonces, {"from": admin})

    etas = [tx.timestamp + delay for delay in delays]

    for i in range(len(targets)):
        tx_hash = timeLock.getTxHash(targets[i], values[i], data[i], etas[i], nonces[i])

        assert timeLock.queued(tx_hash)


def test_batch_queue_not_admin(timeLock, user):
    with brownie.reverts("!admin"):
        timeLock.batchQueue([], [], [], [], [], {"from": user})


def test_batch_queue_invalid_inputs(timeLock, admin):
    with brownie.reverts("targets.length = 0"):
        timeLock.batchQueue([], [], [], [], [], {"from": admin})

    with brownie.reverts("values.length != targets.length"):
        timeLock.batchQueue([ZERO_ADDRESS], [], [], [], [], {"from": admin})

    with brownie.reverts("data.length != targets.length"):
        timeLock.batchQueue([ZERO_ADDRESS], [0], [], [], [], {"from": admin})

    with brownie.reverts("delays.length != targets.length"):
        timeLock.batchQueue([ZERO_ADDRESS], [0], [""], [], [], {"from": admin})

    with brownie.reverts("nonces.length != targets.length"):
        timeLock.batchQueue([ZERO_ADDRESS], [0], [""], [0], [], {"from": admin})
