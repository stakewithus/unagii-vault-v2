import brownie
from brownie import ZERO_ADDRESS


def test_borrow_from_vault(fundManager, token, testVault, admin, keeper, worker, user):
    vault = testVault

    with brownie.reverts("!auth"):
        fundManager.borrowFromVault(0, {"from": user})

    token.mint(vault, 1000)

    def snapshot():
        return {"token": {"fundManager": token.balanceOf(fundManager)}}

    # admin can call
    amount = 1

    before = snapshot()
    tx = fundManager.borrowFromVault(amount, {"from": admin})
    after = snapshot()

    borrowed = after["token"]["fundManager"] - before["token"]["fundManager"]
    assert tx.events["BorrowFromVault"].values() == [vault, amount, borrowed]

    # keeper can call
    fundManager.borrowFromVault(amount, {"from": keeper})

    # worker can call
    fundManager.borrowFromVault(amount, {"from": worker})
