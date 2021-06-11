import brownie
import pytest


def test_set_symbol(uToken, user):
    timeLock = uToken.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        uToken.setSymbol("TEST123", {"from": user})

    uToken.setSymbol("TEST123", {"from": timeLock})
    assert uToken.symbol() == "TEST123"
