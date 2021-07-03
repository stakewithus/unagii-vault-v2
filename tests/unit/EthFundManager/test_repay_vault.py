import brownie
from brownie import ZERO_ADDRESS


def test_repay_vault(ethFundManager, testEthVault, admin, worker, user):
    fundManager = ethFundManager
    vault = testEthVault
    timeLock = fundManager.timeLock()
    user.transfer(fundManager, 1000)

    with brownie.reverts("!auth"):
        fundManager.repayVault(0, 0, {"from": user})

    with brownie.reverts("repaid < min"):
        fundManager.repayVault(0, 100, {"from": admin})

    def snapshot():
        return {"eth": {"fundManager": fundManager.balance()}}

    # time lock can call
    amount = 1

    before = snapshot()
    tx = fundManager.repayVault(amount, 1, {"from": timeLock})
    after = snapshot()

    repaid = before["eth"]["fundManager"] - after["eth"]["fundManager"]
    assert tx.events["RepayVault"].values() == [vault, amount, repaid]

    # admin can call
    fundManager.repayVault(amount, 1, {"from": admin})

    # worker can call
    fundManager.repayVault(amount, 1, {"from": worker})
