import brownie
from brownie import ZERO_ADDRESS


def test_borrow_from_vault(fundManager, token, testVault, admin, keeper, worker, user):
    vault = testVault

    token.mint(vault, 1000)

    with brownie.reverts("!auth"):
        fundManager.borrowFromVault(0, 0, {"from": user})

    with brownie.reverts("borrowed < min"):
        fundManager.borrowFromVault(0, 100, {"from": admin})

    def snapshot():
        return {"token": {"fundManager": token.balanceOf(fundManager)}}

    # admin can call
    amount = 1

    before = snapshot()
    tx = fundManager.borrowFromVault(amount, 1, {"from": admin})
    after = snapshot()

    borrowed = after["token"]["fundManager"] - before["token"]["fundManager"]
    assert tx.events["BorrowFromVault"].values() == [vault, amount, borrowed]

    # keeper can call
    fundManager.borrowFromVault(amount, 1, {"from": keeper})

    # worker can call
    fundManager.borrowFromVault(amount, 1, {"from": worker})
