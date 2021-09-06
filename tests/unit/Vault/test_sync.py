import brownie
from brownie import ZERO_ADDRESS
from brownie.test import given, strategy
import pytest


@pytest.fixture(scope="function", autouse=True)
def setup(fn_isolation, vault, token, admin, testStrategy, user):
    pass


def test_sync_not_auth(vault, user):
    with brownie.reverts("!auth"):
        vault.sync(ZERO_ADDRESS, 0, 0, {"from": user})


def test_sync_not_active_strategy(vault, worker):
    with brownie.reverts("!active strategy"):
        vault.sync(ZERO_ADDRESS, 0, 0, {"from": worker})


def test_sync_total_assets_min_max(vault, worker, admin, token, testStrategy):
    timeLock = vault.timeLock()
    strategy = testStrategy

    vault.approveStrategy(strategy, {"from": timeLock})
    vault.activateStrategy(strategy, 1, {"from": admin})

    token.mint(strategy, 100, {"from": admin})
    assert strategy.totalAssets() >= 100

    # test min
    with brownie.reverts("total out of range"):
        vault.sync(strategy, 101, 101, {"from": worker})

    # test max
    with brownie.reverts("total out of range"):
        vault.sync(strategy, 99, 99, {"from": worker})


@given(
    deposit_amount=strategy("uint256", min_value=1, max_value=2 ** 64 - 1),
    gain=strategy("uint256", min_value=0, max_value=2 ** 64 - 1),
    loss=strategy("uint256", min_value=0, max_value=2 ** 64 - 1),
)
def test_sync(
    vault, token, testStrategy, admin, worker, user, deposit_amount, gain, loss
):
    timeLock = vault.timeLock()
    strategy = testStrategy

    if not vault.strategies(strategy)["approved"]:
        vault.approveStrategy(strategy, {"from": timeLock})

    if not vault.strategies(strategy)["active"]:
        vault.activateStrategy(strategy, 1, {"from": admin})

    # deposit into vault
    token.mint(user, deposit_amount)
    token.approve(vault, deposit_amount, {"from": user})
    vault.deposit(deposit_amount, 1, {"from": user})

    # borrow
    vault.borrow(deposit_amount, {"from": strategy})

    def snapshot():
        return {
            "token": {
                "vault": token.balanceOf(vault),
                "strategy": token.balanceOf(strategy),
            },
            "vault": {
                "totalAssets": vault.totalAssets(),
                "totalDebt": vault.totalDebt(),
                "lockedProfit": vault.lockedProfit(),
                "strategy": {"debt": vault.strategies(strategy)["debt"]},
            },
        }

    # test gain
    token.mint(strategy, gain)
    total = strategy.totalAssets()

    before = snapshot()
    tx = vault.sync(strategy, total, total, {"from": worker})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"]
    assert after["token"]["strategy"] == before["token"]["strategy"]

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] + gain
    assert after["vault"]["totalDebt"] == before["vault"]["totalDebt"] + gain
    assert after["vault"]["lockedProfit"] >= before["vault"]["lockedProfit"] + gain
    assert (
        after["vault"]["strategy"]["debt"] == before["vault"]["strategy"]["debt"] + gain
    )

    assert vault.lastSync() == tx.timestamp

    assert tx.events["Sync"].values() == [
        strategy.address,
        total,
        before["vault"]["strategy"]["debt"],
        vault.lockedProfit(),
    ]

    # test loss
    _loss = min(loss, vault.totalDebt())
    token.burn(strategy, _loss, {"from": admin})
    total = strategy.totalAssets()

    before = snapshot()
    tx = vault.sync(strategy, total, total, {"from": worker})
    after = snapshot()

    assert after["token"]["vault"] == before["token"]["vault"]
    assert after["token"]["strategy"] == before["token"]["strategy"]

    assert after["vault"]["totalAssets"] == before["vault"]["totalAssets"] - _loss
    assert after["vault"]["totalDebt"] == before["vault"]["totalDebt"] - _loss

    if before["vault"]["lockedProfit"] > _loss:
        assert after["vault"]["lockedProfit"] == before["vault"]["lockedProfit"] - _loss
    else:
        assert after["vault"]["lockedProfit"] == 0

    assert (
        after["vault"]["strategy"]["debt"]
        == before["vault"]["strategy"]["debt"] - _loss
    )

    assert vault.lastSync() == tx.timestamp

    assert tx.events["Sync"].values() == [
        strategy.address,
        total,
        before["vault"]["strategy"]["debt"],
        vault.lockedProfit(),
    ]
