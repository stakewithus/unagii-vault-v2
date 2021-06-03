import brownie
import pytest


def test_set_pause(vault, admin, guardian, user):
    # not admin
    with brownie.reverts("!auth"):
        vault.setPause(True, {"from": user})

    # guadian can pause
    vault.setPause(False, {"from": guardian})
    assert not vault.paused()

    # admin can pause
    vault.setPause(True, {"from": admin})
    assert vault.paused()
