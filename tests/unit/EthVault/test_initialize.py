import brownie
from brownie import ZERO_ADDRESS

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_initialize_no_old_vault(EthVault, uEth, admin, guardian, user):
    vault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})

    # not time lock or admin
    with brownie.reverts("!auth"):
        vault.initialize({"from": user})

    tx = vault.initialize({"from": admin})

    assert vault.lastReport() == tx.timestamp
    assert vault.initialized() == True

    with brownie.reverts("initialized"):
        vault.initialize({"from": admin})


def test_initialize_old_vault(
    EthVault, uEth, admin, guardian, user, TestEthFundManager
):
    oldVault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})
    vault = EthVault.deploy(uEth, guardian, oldVault, {"from": admin})

    # set old vault balance > 0
    oldVault.initialize({"from": admin})

    uEth.setMinter(oldVault, {"from": uEth.timeLock()})
    oldVault.setPause(False, {"from": admin})
    oldVault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    oldVault.deposit(100, 0, {"from": user, "value": 100})

    # test not old vault
    with brownie.reverts("!old vault"):
        vault.initialize({"from": user})

    # test uEth minter != new vault
    with brownie.reverts("minter != self"):
        vault.initialize({"from": oldVault})

    uEth.setMinter(vault, {"from": uEth.timeLock()})

    # test fund manager != old vault fund manager
    fundManager = TestEthFundManager.deploy(oldVault, ETH, {"from": admin})
    oldVault.setFundManager(fundManager, {"from": oldVault.timeLock()})

    with brownie.reverts("fund manager != old vault fund manager"):
        vault.initialize({"from": oldVault})

    # test fund manager vault != self
    fundManager.setVault(vault)
    vault.setFundManager(fundManager, {"from": vault.timeLock()})

    fundManager.setVault(ZERO_ADDRESS)
    with brownie.reverts("fund manager vault != self"):
        vault.initialize({"from": oldVault})

    fundManager.setVault(vault)

    # test ETH sent from old vault < balanceOfVault of old vault
    with brownie.reverts("value < vault"):
        vault.initialize({"from": oldVault})

    # test initialize
    def snapshot():
        return {
            "old": {
                "balanceOfVault": oldVault.balanceOfVault(),
                "debt": oldVault.debt(),
                "lockedProfit": oldVault.lockedProfit(),
                "lastReport": oldVault.lastReport(),
            },
            "new": {
                "balanceOfVault": vault.balanceOfVault(),
                "debt": vault.debt(),
                "lockedProfit": vault.lockedProfit(),
                "lastReport": vault.lastReport(),
            },
        }

    before = snapshot()
    vault.initialize({"from": oldVault, "amount": oldVault.balanceOfVault()})
    after = snapshot()

    assert after["new"]["balanceOfVault"] == before["old"]["balanceOfVault"]
    assert after["new"]["debt"] == before["old"]["debt"]
    assert after["new"]["lockedProfit"] == before["old"]["lockedProfit"]
    assert after["new"]["lastReport"] == before["old"]["lastReport"]
    assert vault.initialized()