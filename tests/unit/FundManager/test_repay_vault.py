import brownie
from brownie import ZERO_ADDRESS


def test_repay_vault(fundManager, token, testVault, admin, worker, user):
    vault = testVault
    timeLock = fundManager.timeLock()
    token.mint(fundManager, 1000)

    with brownie.reverts("!auth"):
        fundManager.repayVault(0, 0, {"from": user})

    with brownie.reverts("repaid < min"):
        fundManager.repayVault(0, 100, {"from": admin})

    def snapshot():
        return {"token": {"fundManager": token.balanceOf(fundManager)}}

    # time lock can call
    amount = 1

    before = snapshot()
    tx = fundManager.repayVault(amount, 1, {"from": timeLock})
    after = snapshot()

    repaid = before["token"]["fundManager"] - after["token"]["fundManager"]
    assert tx.events["RepayVault"].values() == [vault, amount, repaid]

    # admin can call
    fundManager.repayVault(amount, 1, {"from": admin})

    # worker can call
    fundManager.repayVault(amount, 1, {"from": worker})
