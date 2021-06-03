import brownie
import pytest


def test_set_next_minter(accounts, uToken, minter):
    # not minter
    with brownie.reverts("!minter"):
        uToken.setNextMinter(accounts[1], {"from": accounts[1]})

    # next minter is current minter
    with brownie.reverts("next minter = current"):
        uToken.setNextMinter(minter, {"from": minter})

    uToken.setNextMinter(accounts[1], {"from": minter})
    assert uToken.nextMinter(), accounts[1]
