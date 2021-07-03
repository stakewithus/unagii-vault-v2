import brownie
import pytest

ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_set_vault(ethFundManager, testEthVault, user):
    fundManager = ethFundManager
    vault = testEthVault
    timeLock = fundManager.timeLock()

    with brownie.reverts("!time lock"):
        fundManager.setVault(user, {"from": user})

    # use user's address
    vault.setToken(user, {"from": timeLock})
    with brownie.reverts("vault token != ETH"):
        fundManager.setVault(vault, {"from": timeLock})

    vault.setToken(ETH, {"from": timeLock})

    tx = fundManager.setVault(vault, {"from": timeLock})
    assert fundManager.vault() == vault
    assert tx.events["SetVault"].values() == [vault]
