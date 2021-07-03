import brownie
from brownie import ZERO_ADDRESS


def test_report_to_vault(ethFundManager, testEthVault, admin, worker, user):
    fundManager = ethFundManager
    vault = testEthVault
    timeLock = fundManager.timeLock()
    user.transfer(fundManager, 1000)

    with brownie.reverts("!auth"):
        fundManager.reportToVault(0, 0, {"from": user})

    # total < min
    with brownie.reverts("total not in range"):
        fundManager.reportToVault(1001, 1000, {"from": timeLock})

    # total > min
    with brownie.reverts("total not in range"):
        fundManager.reportToVault(0, 999, {"from": timeLock})

    # gain > 0
    vault.setDebt(900)

    total = 1000
    debt = 900
    gain = 100
    loss = 0

    tx = fundManager.reportToVault(0, 2 ** 256 - 1, {"from": timeLock})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # loss > 0
    vault.setDebt(1200)

    total = 1000
    debt = 1200
    gain = 0
    loss = 200

    tx = fundManager.reportToVault(0, 2 ** 256 - 1, {"from": timeLock})
    assert tx.events["ReportToVault"].values() == [vault, total, debt, gain, loss]
    assert vault.gain() == gain
    assert vault.loss() == loss

    # admin can call
    fundManager.reportToVault(0, 2 ** 256 - 1, {"from": admin})

    # worker can call
    fundManager.reportToVault(0, 2 ** 256 - 1, {"from": worker})
