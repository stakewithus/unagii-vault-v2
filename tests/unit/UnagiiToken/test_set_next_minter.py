import brownie


def test_set_next_minter(accounts, uToken, admin):
    # not minter
    with brownie.reverts("!minter"):
        uToken.setNextMinter(accounts[1], {"from": accounts[1]})

    # next minter is current minter
    with brownie.reverts("next minter = current"):
        uToken.setNextMinter(admin, {"from": admin})

    uToken.setNextMinter(accounts[1], {"from": admin})
    assert uToken.nextMinter(), accounts[1]
