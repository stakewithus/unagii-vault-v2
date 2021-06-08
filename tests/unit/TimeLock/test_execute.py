import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_execute(chain, timeLock, testTimeLock, admin):
    value = 1
    # data = ""
    data = testTimeLock.test.encode_input("0x1212")
    delay = 24 * 3600
    nonce = 0

    tx = timeLock.queue(testTimeLock, value, data, delay, nonce, {"from": admin})

    eta = tx.timestamp + delay
    txHash = timeLock.getTxHash(testTimeLock, value, data, eta, nonce)

    with brownie.reverts("eta < now"):
        timeLock.execute(testTimeLock, value, data, eta, nonce, {"from": admin})

    chain.sleep(delay)

    # test target.call fails
    testTimeLock.setFail(True)

    with brownie.reverts("tx failed"):
        timeLock.execute(
            testTimeLock, value, data, eta, nonce, {"from": admin, "value": value}
        )

    testTimeLock.setFail(False)
    tx = timeLock.execute(
        testTimeLock, value, data, eta, nonce, {"from": admin, "value": value}
    )

    assert testTimeLock.data() == "0x1212"
    assert testTimeLock.value() == value
    assert not timeLock.queued(txHash)
    assert len(tx.events) == 1
    assert tx.events["Log"].values() == [
        txHash,
        testTimeLock,
        value,
        data,
        eta,
        nonce,
        1,
    ]

    # test expired
    nonce += 1
    tx = timeLock.queue(testTimeLock, value, data, delay, nonce, {"from": admin})
    eta = tx.timestamp + delay
    txHash = timeLock.getTxHash(testTimeLock, value, data, eta, nonce)

    chain.sleep(24 * 24 * 3600)

    with brownie.reverts("eta expired"):
        timeLock.execute(
            testTimeLock, value, data, eta, nonce, {"from": admin, "value": value}
        )


def test_execute_not_admin(timeLock, user):
    with brownie.reverts("!admin"):
        timeLock.execute(ZERO_ADDRESS, 0, "", 0, 0, {"from": user})


def test_execute_not_queued(timeLock, admin):
    with brownie.reverts("!queued"):
        timeLock.execute(ZERO_ADDRESS, 0, "", 0, 0, {"from": admin})