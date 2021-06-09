import brownie
from brownie import ZERO_ADDRESS


def test_repay_vault(fundManager, token, testVault, admin, keeper, worker, user):
    vault = testVault

    with brownie.reverts("!auth"):
        fundManager.repayVault(0, {"from": user})

    token.mint(fundManager, 1000)

    def snapshot():
        return {"token": {"fundManager": token.balanceOf(fundManager)}}

    # admin can call
    amount = 1

    before = snapshot()
    tx = fundManager.repayVault(amount, {"from": admin})
    after = snapshot()

    repaid = before["token"]["fundManager"] - after["token"]["fundManager"]
    assert tx.events["RepayVault"].values() == [vault, amount, repaid]

    # keeper can call
    fundManager.repayVault(amount, {"from": keeper})

    # worker can call
    fundManager.repayVault(amount, {"from": worker})
