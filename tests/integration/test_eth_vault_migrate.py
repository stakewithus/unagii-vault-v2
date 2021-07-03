import brownie
import pytest

DELAY = 24 * 3600


def test_vault_migration(
    chain,
    setup_eth,
    timeLock,
    ethVault,
    uEth,
    guardian,
    admin,
    ethFundManager,
    EthVault,
    user,
):
    vault = ethVault
    fundManager = ethFundManager
    uToken = uEth

    # setup vault balance > 0
    vault.deposit(100, 0, {"from": user, "value": 100})

    newVault = EthVault.deploy(uToken, guardian, vault, {"from": admin})
    # set new vault time lock
    newVault.setNextTimeLock(timeLock, {"from": admin})

    data = newVault.acceptTimeLock.encode_input()
    tx = timeLock.queue(newVault, 0, data, DELAY, 0, {"from": admin})
    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)
    timeLock.execute(newVault, 0, data, eta, 0, {"from": admin})

    vault.setPause(True, {"from": admin})

    # queue migration transactions
    targets = [uToken, fundManager, newVault, vault]

    values = [0, 0, 0, 0]

    data = [
        uToken.setMinter.encode_input(newVault),
        fundManager.setVault.encode_input(newVault),
        newVault.setFundManager.encode_input(fundManager),
        vault.migrate.encode_input(newVault),
    ]

    delays = [DELAY, DELAY, DELAY, DELAY]
    nonces = [0, 0, 0, 0]

    tx = timeLock.batchQueue(
        targets,
        values,
        data,
        delays,
        nonces,
        {"from": admin},
    )

    eta = tx.timestamp + DELAY
    chain.sleep(DELAY)

    # execute migration transactions
    def snapshot():
        return {
            "eth": {
                "old": vault.balance(),
                "new": newVault.balance(),
            },
            "old": {
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
                "lockedProfit": vault.lockedProfit(),
                "lastReport": vault.lastReport(),
            },
            "new": {
                "balanceOfVault": newVault.balanceOfVault(),
                "debt": newVault.debt(),
                "lockedProfit": newVault.lockedProfit(),
                "lastReport": newVault.lastReport(),
            },
        }

    etas = [eta, eta, eta, eta]

    before = snapshot()
    tx = timeLock.batchExecute(
        targets,
        values,
        data,
        etas,
        nonces,
        {"from": admin},
    )
    after = snapshot()

    assert after["eth"]["new"] == before["eth"]["old"]
    assert after["eth"]["old"] == 0

    assert after["new"]["balanceOfVault"] == before["old"]["balanceOfVault"]
    assert after["new"]["debt"] == before["old"]["debt"]
    assert after["new"]["lockedProfit"] == before["old"]["lockedProfit"]
    assert after["new"]["lastReport"] == before["old"]["lastReport"]

    assert after["old"]["balanceOfVault"] == 0
    assert after["old"]["debt"] == 0
    assert after["old"]["lockedProfit"] == 0

    assert uToken.minter() == newVault
    assert fundManager.vault() == newVault
    assert newVault.fundManager() == fundManager