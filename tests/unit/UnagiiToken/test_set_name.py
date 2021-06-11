import brownie
import pytest


def test_set_name(uToken, user):
    timeLock = uToken.timeLock()

    # not time lock
    with brownie.reverts("!time lock"):
        uToken.setName("test123", {"from": user})

    uToken.setName("test123", {"from": timeLock})
    assert uToken.name() == "test123"
