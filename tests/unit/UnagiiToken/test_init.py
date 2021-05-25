import brownie


def test_init(uToken, token, admin):
    assert uToken.minter() == admin
    assert uToken.token() == token.address
    assert uToken.name() == "unagii_v2_" + token.name()
    assert uToken.symbol() == "u2" + token.symbol()
    assert uToken.decimals() == token.decimals()