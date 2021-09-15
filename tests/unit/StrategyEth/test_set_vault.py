import brownie
from brownie import ZERO_ADDRESS


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_set_vault(strategyEthTest, TestEthVault, admin, user):
    strategy = strategyEthTest
    timeLock = strategy.timeLock()
    vault = strategy.vault()
    newVault = TestEthVault.deploy({"from": admin})

    # not time lock
    with brownie.reverts("!time lock"):
        strategy.setVault(newVault, {"from": user})

    # new vault token != ETH
    newVault._setToken_(ZERO_ADDRESS)
    with brownie.reverts("new vault token != ETH"):
        strategy.setVault(newVault, {"from": timeLock})

    newVault._setToken_(ETH)

    tx = strategy.setVault(newVault, {"from": timeLock})

    assert tx.events["SetVault"].values() == [newVault]
