import brownie
from brownie import ZERO_ADDRESS
import pytest

from eth_account import Account
from eth_account.messages import encode_structured_data

AMOUNT = 2 ** 256 - 1


def test_owner_zero_address(uToken, user):
    with brownie.reverts("owner = 0 address"):
        uToken.permit(ZERO_ADDRESS, ZERO_ADDRESS, 0, 0, 0, 0, 0, {"from": user})


def test_deadline(uToken, user):
    with brownie.reverts("expired"):
        uToken.permit(user, ZERO_ADDRESS, 0, 0, 0, 0, 0, {"from": user})


def sign(chain, uToken, owner, spender, allowance, deadline, nonce):
    name = "unagii"
    version = "0.1.1"

    data = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"},
            ],
            "Permit": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "nonce", "type": "uint256"},
                {"name": "deadline", "type": "uint256"},
            ],
        },
        "domain": {
            "name": name,
            "version": version,
            # "chainId": chain.id,
            # https://github.com/trufflesuite/ganache/issues/1643
            "chainId": 1,
            "verifyingContract": str(uToken),
        },
        "primaryType": "Permit",
        "message": {
            "owner": owner.address,
            "spender": spender,
            "value": allowance,
            "nonce": nonce,
            "deadline": deadline,
        },
    }

    msg = encode_structured_data(data)
    return owner.sign_message(msg)


def test_permit(chain, uToken, user):
    owner = Account.create()
    deadline = chain[-1].timestamp + 3600

    nonce = uToken.nonces(owner.address)
    sig = sign(chain, uToken, owner, user.address, AMOUNT, deadline, nonce)

    assert uToken.allowance(owner.address, user) == 0
    uToken.permit(
        owner.address, user, AMOUNT, deadline, sig.v, sig.r, sig.s, {"from": user}
    )
    assert uToken.allowance(owner.address, user) == AMOUNT
    assert uToken.nonces(owner.address) == nonce + 1


def test_permit_wrong_signature(chain, uToken, user):
    owner = Account.create()

    deadline = 2 ** 256 - 1
    nonce = uToken.nonces(owner.address)
    sig = sign(chain, uToken, owner, user.address, 0, deadline, nonce)

    with brownie.reverts("invalid signature"):
        uToken.permit(
            owner.address, user, AMOUNT, deadline, sig.v, sig.r, sig.s, {"from": user}
        )
