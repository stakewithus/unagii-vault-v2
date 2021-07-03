import brownie
from brownie import ZERO_ADDRESS


def test_borrow_from_vault(ethFundManager, testEthVault, admin, worker, user):
    fundManager = ethFundManager
    vault = testEthVault
    timeLock = fundManager.timeLock()

    user.transfer(vault, 1000)

    with brownie.reverts("!auth"):
        fundManager.borrowFromVault(0, 0, {"from": user})

    with brownie.reverts("borrowed < min"):
        fundManager.borrowFromVault(0, 100, {"from": admin})

    def snapshot():
        return {"eth": {"fundManager": fundManager.balance()}}

    # time lock can call
    amount = 1

    before = snapshot()
    tx = fundManager.borrowFromVault(amount, 1, {"from": timeLock})
    after = snapshot()

    borrowed = after["eth"]["fundManager"] - before["eth"]["fundManager"]
    assert tx.events["BorrowFromVault"].values() == [vault, amount, borrowed]

    # admin can call
    fundManager.borrowFromVault(amount, 1, {"from": admin})

    # worker can call
    fundManager.borrowFromVault(amount, 1, {"from": worker})
