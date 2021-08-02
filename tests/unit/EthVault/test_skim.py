import brownie
import pytest


def test_skim(ethVault, admin, user, testEthFundManager):
    vault = ethVault
    timeLock = vault.timeLock()
    fundManager = testEthFundManager

    # not auth
    with brownie.reverts("!time lock"):
        vault.skim({"from": user})

    vault.setFundManager(fundManager, {"from": timeLock})

    user.transfer(fundManager, 123)
    fundManager.sendEth(vault, 123)

    diff = vault.balance() - vault.balanceOfVault()

    def snapshot():
        return {
            "vault": {"balanceOfVault": vault.balanceOfVault()},
            "eth": {
                "admin": admin.balance(),
                "vault": vault.balance(),
            },
        }

    before = snapshot()
    vault.skim({"from": admin})
    after = snapshot()

    assert after["eth"]["admin"] == before["eth"]["admin"] + diff
    assert after["eth"]["vault"] == before["eth"]["vault"] - diff
    assert after["vault"]["balanceOfVault"] == before["vault"]["balanceOfVault"]
    assert after["vault"]["balanceOfVault"] == after["eth"]["vault"]
