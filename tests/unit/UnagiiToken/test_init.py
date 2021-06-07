import brownie


def test_init(uToken, token, admin, minter):
    assert uToken.admin() == admin
    assert uToken.minter() == minter
    assert uToken.token() == token.address
    assert uToken.name() == "unagii_" + token.name() + "_v2"
    assert uToken.symbol() == "u" + token.symbol() + "v2"
    assert uToken.decimals() == token.decimals()