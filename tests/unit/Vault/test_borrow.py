import brownie

# max active strategies
N = 20


def test_borrow(vault, token, admin, guardian, testStrategy, user):
    strategy = testStrategy
    timeLock = vault.timeLock()

    deposit_amount = 100

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    # revert if not active strategy
    with brownie.reverts("!active strategy"):
        vault.borrow(0, {"from": strategy})

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 1, {"from": admin})

    # borrow = 0
    with brownie.reverts("borrow = 0"):
        vault.borrow(0, {"from": strategy})

    # borrow = 0 if paused
    vault.setPause(True, {"from": guardian})
    calc = vault.calcMaxBorrow(strategy)
    assert calc == 0

    with brownie.reverts("borrow = 0"):
        vault.borrow(1, {"from": strategy})

    vault.setPause(False, {"from": guardian})

    # borrow = 0 if total debt ratio = 0
    vault.setDebtRatios([0 for i in range(N)], {"from": admin})
    calc = vault.calcMaxBorrow(strategy)
    assert calc == 0

    with brownie.reverts("borrow = 0"):
        vault.borrow(1, {"from": strategy})

    vault.setDebtRatios([1 for i in range(N)], {"from": admin})

    # borrow = 0 if balance of vault <= min reserve
    vault.setMinReserve(10000, {"from": admin})
    calc = vault.calcMaxBorrow(strategy)
    assert calc == 0

    with brownie.reverts("borrow = 0"):
        vault.borrow(1, {"from": strategy})

    vault.setMinReserve(500, {"from": admin})

    # test borrow > 0
    calc = vault.calcMaxBorrow(strategy)
    assert calc > 0

    def snapshot():
        strat = vault.strategies(strategy)

        return {
            "token": {
                "vault": token.balanceOf(vault),
                "strategy": token.balanceOf(strategy),
            },
            "vault": {
                "totalAssets": vault.totalAssets(),
                "totalDebt": vault.totalDebt(),
                "strategy": {"debt": strat["debt"]},
            },
        }

    before = snapshot()
    tx = vault.borrow(2 ** 256 - 1, {"from": strategy})
    after = snapshot()

    diff = before["token"]["vault"] - after["token"]["vault"]
    assert diff == calc
    assert after["token"]["vault"] == before["token"]["vault"] - diff
    assert after["token"]["strategy"] == before["token"]["strategy"] + diff
    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"]
    assert after["vault"]["totalDebt"] == before["vault"]["totalDebt"] + diff
    assert (
        after["vault"]["strategy"]["debt"] == before["vault"]["strategy"]["debt"] + diff
    )

    assert tx.events["Borrow"].values() == [strategy, diff]

    # borrow = 0 if debt >= limit
    calc = vault.calcMaxBorrow(strategy)
    assert calc == 0

    with brownie.reverts("borrow = 0"):
        vault.borrow(2 ** 256 - 1, {"from": strategy})