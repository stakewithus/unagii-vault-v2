import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_accept_minter(accounts, uToken, admin):
    uToken.setNextMinter(accounts[1], {"from": admin})

    # not next minter
    with brownie.reverts("!next minter"):
        uToken.acceptMinter({"from": accounts[0]})

    uToken.acceptMinter({"from": accounts[1]})
    assert uToken.minter() == accounts[1]
    assert uToken.nextMinter() == ZERO_ADDRESS
