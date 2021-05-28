import brownie
import pytest

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_revoke_strategy(vault, token, admin, timeLock, guardian, strategy, user):
    vault.approveStrategy(strategy, 1, 2, 3, {"from": timeLock})

    # revert if not authorized
    with brownie.reverts("!auth"):
        vault.revokeStrategy(strategy, {"from": user})

    vault.revokeStrategy(strategy, {"from": guardian})
    strat = vault.strategies(strategy)

    assert not strat["approved"]

    # revert if not approved
    with brownie.reverts("!approved"):
        vault.revokeStrategy(strategy, {"from": guardian})
