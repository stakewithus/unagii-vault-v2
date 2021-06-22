import brownie
from brownie import ZERO_ADDRESS


def test_migrate(
    Vault, token, uToken, admin, guardian, user, TestToken, UnagiiToken, TestFundManager
):
    vault = Vault.deploy(token, uToken, guardian, ZERO_ADDRESS, {"from": admin})
    newVault = Vault.deploy(token, uToken, guardian, vault, {"from": admin})

    # test not time lock
    with brownie.reverts("!time lock"):
        vault.migrate(newVault, {"from": user})

    timeLock = vault.timeLock()

    # test not initialized
    with brownie.reverts("!initialized"):
        vault.migrate(newVault, {"from": timeLock})

    uToken.setMinter(vault, {"from": uToken.timeLock()})
    vault.initialize()

    # test not paused
    vault.setPause(False)

    with brownie.reverts("!paused"):
        vault.migrate(newVault, {"from": timeLock})

    vault.setPause(True)

    # test new vault token != token
    _token = TestToken.deploy("test", "TEST", 18, {"from": admin})
    _uToken = UnagiiToken.deploy(_token, {"from": admin})
    _newVault = Vault.deploy(_token, _uToken, guardian, ZERO_ADDRESS, {"from": admin})

    with brownie.reverts("new vault token != token"):
        vault.migrate(_newVault, {"from": timeLock})

    # test new vault uToken != uToken
    _uToken = UnagiiToken.deploy(token, {"from": admin})
    _newVault = Vault.deploy(token, _uToken, guardian, ZERO_ADDRESS, {"from": admin})

    with brownie.reverts("new vault uToken != uToken"):
        vault.migrate(_newVault, {"from": timeLock})

    # test uToken minter != new vault
    uToken.setMinter(vault, {"from": uToken.timeLock()})

    with brownie.reverts("minter != new vault"):
        vault.migrate(newVault, {"from": timeLock})

    uToken.setMinter(newVault, {"from": uToken.timeLock()})

    # test new vault fund manager != old vault fund manager
    fundManager = TestFundManager.deploy(vault, token, {"from": admin})
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

    # test bal < vault
    # set old vault balance > 0
    uToken.setMinter(vault, {"from": uToken.timeLock()})
    vault.setPause(False, {"from": admin})
    vault.setDepositLimit(2 ** 256 - 1, {"from": admin})

    token.mint(user, 100)
    token.approve(vault, 100, {"from": user})
    vault.deposit(100, 0, {"from": user})

    # force bal < balanceOfVault
    token.burn(vault, 1)

    vault.setPause(True, {"from": admin})
    uToken.setMinter(newVault, {"from": uToken.timeLock()})

    with brownie.reverts("bal < vault"):
        vault.migrate(newVault, {"from": timeLock})

    token.mint(vault, 1)

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