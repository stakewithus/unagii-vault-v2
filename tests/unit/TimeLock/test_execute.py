import brownie
from brownie import ZERO_ADDRESS
import pytest


def test_execute(chain, timeLock, txTest, admin):
    value = 1
    # data = ""
    data = txTest.test.encode_input("0x1212")
    delay = 24 * 3600
    nonce = 0

    tx = timeLock.queue(txTest, value, data, delay, nonce, {"from": admin})

    eta = tx.timestamp + delay
    txHash = timeLock.getTxHash(txTest, value, data, eta, nonce)

    with brownie.reverts("bal < value"):
        timeLock.execute(txTest, value, data, eta, nonce, {"from": admin, "value": 0})

    with brownie.reverts("eta < now"):
        timeLock.execute(
            txTest, value, data, eta, nonce, {"from": admin, "value": value}
        )

    chain.sleep(delay)

    # test target.call fails
    txTest.setFail(True)

    with brownie.reverts("tx failed"):
        timeLock.execute(
            txTest, value, data, eta, nonce, {"from": admin, "value": value}
        )

    txTest.setFail(False)
    tx = timeLock.execute(
        txTest, value, data, eta, nonce, {"from": admin, "value": value}
    )

    assert txTest.data() == "0x1212"
    assert txTest.value() == value
    assert not timeLock.queued(txHash)
    assert len(tx.events) == 1
    assert tx.events["Log"].values() == [
        txHash,
        txTest,
        value,
        data,
        eta,
        nonce,
        1,
    ]

    # test expired
    nonce += 1
    tx = timeLock.queue(txTest, value, data, delay, nonce, {"from": admin})
    eta = tx.timestamp + delay
    txHash = timeLock.getTxHash(txTest, value, data, eta, nonce)

    chain.sleep(24 * 24 * 3600)

    with brownie.reverts("eta expired"):
        timeLock.execute(
            txTest, value, data, eta, nonce, {"from": admin, "value": value}
        )


def test_execute_not_admin(timeLock, user):
    with brownie.reverts("!admin"):
        timeLock.execute(ZERO_ADDRESS, 0, "", 0, 0, {"from": user})


def test_execute_not_queued(timeLock, admin):
    with brownie.reverts("!queued"):
        timeLock.execute(ZERO_ADDRESS, 0, "", 0, 0, {"from": admin})