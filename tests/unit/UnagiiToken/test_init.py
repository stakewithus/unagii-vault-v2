import brownie
from brownie import UnagiiToken


def test_init(token, admin):
    uToken = UnagiiToken.deploy(token, {"from": admin})

    assert uToken.timeLock() == admin
    assert uToken.token() == token.address
    assert uToken.name() == "unagii_" + token.name() + "_v2"
    assert uToken.symbol() == "u" + token.symbol() + "v2"
    assert uToken.decimals() == token.decimals()


ETH = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


def test_init_eth(admin):
    uToken = UnagiiToken.deploy(ETH, {"from": admin})

    assert uToken.timeLock() == admin
    assert uToken.token() == ETH
    assert uToken.name() == "unagii_ETH_v2"
    assert uToken.symbol() == "uETHv2"
    assert uToken.decimals() == 18