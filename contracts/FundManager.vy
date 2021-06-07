# @version 0.2.12

"""
@title Unagii FundManager
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20


interface Vault:
    def token() -> address: view
    def debt() -> uint256: view
    def borrow(amount: uint256) -> uint256: nonpayable
    def repay(amount: uint256) -> uint256: nonpayable
    def report(gain: uint256, loss: uint256): nonpayable


event SetNextAdmin:
    nextAdmin: address


event AcceptAdmin:
    admin: address


event SetGuardian:
    guardian: address


event SetKeeper:
    keeper: address


event SetVault:
    vault: address


vault: public(Vault)
token: public(ERC20)
admin: public(address)
nextAdmin: public(address)
guardian: public(address)
keeper: public(address)


@external
def __init__(
    token: address,
    guardian: address,
    keeper: address
):
    self.admin = msg.sender
    self.guardian = guardian
    self.keeper = keeper
    self.token = ERC20(token)


@external
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    self.nextAdmin = nextAdmin
    log SetNextAdmin(nextAdmin)


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    log AcceptAdmin(msg.sender)


@external
def setGuardian(guardian: address):
    assert msg.sender in [self.admin, self.guardian, self.keeper], "!auth"
    self.guardian = guardian
    log SetGuardian(guardian)


@external
def setKeeper(keeper: address):
    assert msg.sender in [self.admin, self.guardian, self.keeper], "!auth"
    self.keeper = keeper
    log SetKeeper(keeper)


# TODO: test migration
@external
def setVault(vault: address):
    assert msg.sender == self.admin, "!admin"
    assert Vault(vault).token() == self.token.address, "vault.token != token"
    self.vault = Vault(vault)
    self.token.approve(vault, MAX_UINT256)
    log SetVault(vault)


@internal
def _safeTransfer(token: address, receiver: address, amount: uint256):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("transfer(address,uint256)"),
            convert(receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(res) > 0:
        assert convert(res, bool), "transfer failed"


@internal
def _safeTransferFrom(
    token: address, owner: address, receiver: address, amount: uint256
):
    res: Bytes[32] = raw_call(
        token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(owner, bytes32),
            convert(receiver, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(res) > 0:
        assert convert(res, bool), "transferFrom failed"

# @internal
# @view
# def _calcOutstandingDebt() -> uint256:
#     if self.paused:
#         return self.debt

#     freeFunds: uint256 = self._calcFreeFunds()
#     limit: uint256 = (MAX_MIN_RESERVE - self.minReserve) * freeFunds / MAX_MIN_RESERVE
#     debt: uint256 = self.debt

#     if debt >= limit:
#         return debt - limit
#     return 0


# # TODO: test
# @external
# def calcOutstandingDebt() -> uint256:
#     return self._calcOutstandingDebt()


@external
def sweep(token: address):
    assert msg.sender in [self.admin, self.keeper], "!auth"
    assert token != self.token.address, "protected"
    self._safeTransfer(token, msg.sender, ERC20(token).balanceOf(self))