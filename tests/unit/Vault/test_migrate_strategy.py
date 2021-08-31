import brownie
from brownie import ZERO_ADDRESS

N = 20  # max active strategies


def test_migrate_strategy(chain, vault, testStrategy, TestStrategy, token, admin, user):
    timeLock = vault.timeLock()

    deposit_amount = 100

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    old = testStrategy
    new = TestStrategy.deploy(vault, token, {"from": admin})

    # fund strat with token
    token.mint(old, 100)

    # test not auth
    with brownie.reverts("!auth"):
        vault.migrateStrategy(old, new, {"from": user})

    # test old strategy not active
    with brownie.reverts("old !active"):
        vault.migrateStrategy(ZERO_ADDRESS, new, {"from": admin})

    vault.approveStrategy(old, {"from": timeLock})
    vault.activateStrategy(old, 1, {"from": timeLock})

    # test new strategy not approved
    with brownie.reverts("new !approved"):
        vault.migrateStrategy(old, new, {"from": admin})

    vault.approveStrategy(new, {"from": timeLock})

    # test new strategy active
    vault.activateStrategy(new, 1, {"from": admin})

    with brownie.reverts("new active"):
        vault.migrateStrategy(old, new, {"from": admin})

    # test new strategy debt > 0
    calc = vault.calcMaxBorrow(new)
    vault.borrow(calc, {"from": new})

    vault.deactivateStrategy(new, {"from": admin})

    with brownie.reverts("new debt != 0"):
        vault.migrateStrategy(old, new, {"from": admin})

    token.approve(vault, calc, {"from": new})
    vault.repay(calc, {"from": new})

    # test migrate strategy
    def snapshot():
        return {
            "queue": [vault.queue(i) for i in range(N)],
            "old": vault.strategies(old),
            "new": vault.strategies(new),
            "token": {
                "old": token.balanceOf(old),
                "new": token.balanceOf(new),
            },
        }

    before = snapshot()
    tx = vault.migrateStrategy(old, new, {"from": admin})
    after = snapshot()

    assert tx.events["MigrateStrategy"].values() == [old, new]

    assert after["new"]["approved"]
    assert after["new"]["active"]
    assert after["new"]["debtRatio"] == before["old"]["debtRatio"]
    assert after["new"]["debt"] == before["old"]["debt"]

    assert after["old"]["approved"]
    assert not after["old"]["active"]
    assert after["old"]["debtRatio"] == 0
    assert after["old"]["debt"] == 0

    assert before["queue"][0] == old
    assert after["queue"][0] == new

    # check migrate was called
    assert after["token"]["new"] == before["token"]["old"]
    assert after["token"]["new"] > 0
    assert after["token"]["old"] == 0
