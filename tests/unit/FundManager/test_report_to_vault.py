import brownie
from brownie import ZERO_ADDRESS


def test_report_to_vault(fundManager, token, testVault, admin, keeper, worker, user):
    vault = testVault
    token.mint(fundManager, 1000)

    with brownie.reverts("!auth"):
        fundManager.reportToVault(0, 0, {"from": user})

    # total < min
    with brownie.reverts("total not in range"):
        fundManager.reportToVault(1001, 1000, {"from": admin})

    # total > min
    with brownie.reverts("total not in range"):
        fundManager.reportToVault(0, 999, {"from": admin})

    # gain > 0
    vault.setDebt(900)

    total = 1000
    debt = 900
    gain = 100
    loss = 0

    tx = fundManager.reportToVault(0, 2 ** 256 - 1, {"from": admin})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # loss > 0
    vault.setDebt(1200)

    total = 1000
    debt = 1200
    gain = 0
    loss = 200

    tx = fundManager.reportToVault(0, 2 ** 256 - 1, {"from": admin})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # admin can call
    fundManager.reportToVault(0, 2 ** 256 - 1, {"from": admin})

    # keeper can call
    fundManager.reportToVault(0, 2 ** 256 - 1, {"from": keeper})

    # worker can call
    fundManager.reportToVault(0, 2 ** 256 - 1, {"from": worker})
