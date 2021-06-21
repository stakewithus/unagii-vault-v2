import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_batch_execute(chain, timeLock, txTest, admin):
    targets = [txTest, txTest]
    values = [1, 2]
    inputs = ["0x1212", "0x2121"]
    data = [txTest.test.encode_input(input) for input in inputs]
    delays = [24 * 3600, 25 * 3600]
    nonces = [0, 1]

    tx = timeLock.batchQueue(targets, values, data, delays, nonces, {"from": admin})

    etas = [tx.timestamp + delay for delay in delays]
    tx_hashes = []
    for i in range(len(targets)):
        tx_hashes.append(
            timeLock.getTxHash(targets[i], values[i], data[i], etas[i], nonces[i])
        )

    chain.sleep(max(delays))

    tx = timeLock.batchExecute(
        targets, values, data, etas, nonces, {"from": admin, "value": sum(values)}
    )

    # check last target
    target = targets[-1]
    tx_hash = tx_hashes[-1]

    assert target.data() == inputs[-1]
    assert txTest.value() == values[-1]

    # check all tx executed
    for tx_hash in tx_hashes:
        assert not timeLock.queued(tx_hash)


def test_batch_execute_not_admin(timeLock, user):
    with brownie.reverts("!admin"):
        timeLock.batchExecute([], [], [], [], [], {"from": user})


def test_batch_execute_invalid_inputs(timeLock, admin):
    with brownie.reverts("targets.length = 0"):
        timeLock.batchExecute([], [], [], [], [], {"from": admin})

    with brownie.reverts("values.length != targets.length"):
        timeLock.batchExecute([ZERO_ADDRESS], [], [], [], [], {"from": admin})

    with brownie.reverts("data.length != targets.length"):
        timeLock.batchExecute([ZERO_ADDRESS], [0], [], [], [], {"from": admin})

    with brownie.reverts("etas.length != targets.length"):
        timeLock.batchExecute([ZERO_ADDRESS], [0], [""], [], [], {"from": admin})

    with brownie.reverts("nonces.length != targets.length"):
        timeLock.batchExecute([ZERO_ADDRESS], [0], [""], [0], [], {"from": admin})
