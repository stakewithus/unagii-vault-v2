import brownie
from brownie import ZERO_ADDRESS


def test_initialize_no_old_vault(Vault, token, uToken, admin, guardian, user):
    vault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})

    # not time lock or admin
    with brownie.reverts("!auth"):
        vault.initialize({"from": user})

    tx = vault.initialize({"from": admin})

    assert vault.lastReport() == tx.timestamp
    assert vault.initialized() == True

    with brownie.reverts("initialized"):
        vault.initialize({"from": admin})


def test_initialize_old_vault(
    Vault, token, uToken, admin, guardian, user, TestFundManager
):
    oldVault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})
    vault = Vault.deploy(token, uToken, guardian, oldVault, {"from": admin})

    # set old vault balance > 0
    uToken.setMinter(oldVault, {"from": uToken.timeLock()})
    oldVault.setPause(False, {"from": admin})
    oldVault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    token.mint(user, 100)
    token.approve(oldVault, 100, {"from": user})
    oldVault.deposit(100, 0, {"from": user})

    # test not old vault
    with brownie.reverts("!old vault"):
        vault.initialize({"from": user})

    # test uToken minter != new vault
    with brownie.reverts("minter != self"):
        vault.initialize({"from": oldVault})

    uToken.setMinter(vault, {"from": uToken.timeLock()})

    # test fund manager != old vault fund manager
    fundManager = TestFundManager.deploy(oldVault, token, {"from": admin})
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

    # test token balance of old vault < balanceOfVault of old vault
    token.burn(oldVault, 1)

    with brownie.reverts("bal < vault"):
        vault.initialize({"from": oldVault})

    token.mint(oldVault, 1)

    # test diff < min
    token.approve(vault, 100, {"from": oldVault})
    token.setFeeOnTransfer(10)

    with brownie.reverts("diff < min"):
        vault.initialize({"from": oldVault})

    # test initialize
    token.setFeeOnTransfer(0)

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
    vault.initialize({"from": oldVault})
    after = snapshot()

    assert after["new"]["balanceOfVault"] == before["old"]["balanceOfVault"]
    assert after["new"]["debt"] == before["old"]["debt"]
    assert after["new"]["lockedProfit"] == before["old"]["lockedProfit"]
    assert after["new"]["lastReport"] == before["old"]["lastReport"]
    assert vault.initialized()