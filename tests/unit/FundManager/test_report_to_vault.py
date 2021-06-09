import brownie
from brownie import ZERO_ADDRESS


def test_report_to_vault(fundManager, token, testVault, admin, keeper, worker, user):
    vault = testVault

    with brownie.reverts("!auth"):
        fundManager.reportToVault({"from": user})

    token.mint(fundManager, 1000)

    # gain > 0
    vault.setDebt(900)

    total = 1000
    debt = 900
    gain = 100
    loss = 0

    tx = fundManager.reportToVault({"from": admin})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # loss > 0
    vault.setDebt(1200)

    total = 1000
    debt = 1200
    gain = 0
    loss = 200

    tx = fundManager.reportToVault({"from": admin})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # admin can call
    fundManager.reportToVault({"from": admin})

    # keeper can call
    fundManager.reportToVault({"from": keeper})

    # worker can call
    fundManager.reportToVault({"from": worker})
