import brownie
from brownie import ZERO_ADDRESS

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_migrate(
    EthVault,
    uEth,
    admin,
    guardian,
    user,
    UnagiiToken,
    TestEthFundManager,
):
    vault = EthVault.deploy(uEth, guardian, ZERO_ADDRESS, {"from": admin})
    newVault = EthVault.deploy(uEth, guardian, vault, {"from": admin})

    # test not time lock
    with brownie.reverts("!time lock"):
        vault.migrate(newVault, {"from": user})

    timeLock = vault.timeLock()

    # test not initialized
    with brownie.reverts("!initialized"):
        vault.migrate(newVault, {"from": timeLock})

    uEth.setMinter(vault, {"from": uEth.timeLock()})
    vault.initialize()

    # test not paused
    vault.setPause(False)

    with brownie.reverts("!paused"):
        vault.migrate(newVault, {"from": timeLock})

    vault.setPause(True)

    # test new vault uToken != uToken
    _uEth = UnagiiToken.deploy(ETH, {"from": admin})
    _newVault = EthVault.deploy(_uEth, guardian, ZERO_ADDRESS, {"from": admin})

    with brownie.reverts("new vault uToken != uToken"):
        vault.migrate(_newVault, {"from": timeLock})

    # test uToken minter != new vault
    uEth.setMinter(vault, {"from": uEth.timeLock()})

    with brownie.reverts("minter != new vault"):
        vault.migrate(newVault, {"from": timeLock})

    uEth.setMinter(newVault, {"from": uEth.timeLock()})

    # test new vault fund manager != old vault fund manager
    fundManager = TestEthFundManager.deploy(vault, ETH, {"from": admin})
    vault.setFundManager(fundManager, {"from": timeLock})

    with brownie.reverts("new vault fund manager != fund manager"):
        vault.migrate(newVault, {"from": timeLock})

    # test fund manager vault != new vault
    fundManager.setVault(newVault)
    newVault.setFundManager(fundManager, {"from": timeLock})
    fundManager.setVault(ZERO_ADDRESS)

    with brownie.reverts("fund manager vault != new vault"):
        vault.migrate(newVault, {"from": timeLock})

    fundManager.setVault(newVault)

    # set old vault balance > 0
    uEth.setMinter(vault, {"from": uEth.timeLock()})
    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    vault.deposit(100, 0, {"from": user, "value": 100})

    vault.setPause(True, {"from": admin})
    uEth.setMinter(newVault, {"from": uEth.timeLock()})

    # test migrate
    def snapshot():
        return {
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

    before = snapshot()
    tx = vault.migrate(newVault, {"from": timeLock})
    after = snapshot()

    assert tx.events["Migrate"].values() == [
        newVault,
        before["old"]["balanceOfVault"],
        before["old"]["debt"],
        before["old"]["lockedProfit"],
    ]

    assert after["old"]["balanceOfVault"] == 0
    assert after["old"]["debt"] == 0
    assert after["old"]["lockedProfit"] == 0