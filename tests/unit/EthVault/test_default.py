import brownie
from brownie import ZERO_ADDRESS


def test_default(ethVault, admin, user):
    vault = ethVault

    with brownie.reverts("!whitelist"):
        user.transfer(vault, 1)

    def snapshot():
        return {"vault": {"balance": vault.balance()}}

    before = snapshot()
    admin.transfer(vault, 1)
    after = snapshot()

    assert after["vault"]["balance"] - before["vault"]["balance"] == 1
