# @version 0.2.12

"""
@title Unagii FundManager
@author stakewith.us
@license AGPL-3.0-or-later
"""

from vyper.interfaces import ERC20


interface Vault:
    def report(): nonpayable


event SetNextAdmin:
    nextAdmin: address


event AcceptAdmin:
    admin: address


event SetTimeLock:
    timeLock: address


vault: public(Vault)
token: public(ERC20)
admin: public(address)
nextAdmin: public(address)
timeLock: public(address)


@external
def __init__(token: address, timeLock: address):
    self.admin = msg.sender
    self.token = ERC20(token)


@external
def setNextAdmin(nextAdmin: address):
    assert msg.sender == self.admin, "!admin"
    assert nextAdmin != self.admin, "next admin = current"
    self.nextAdmin = nextAdmin
    log SetNextAdmin(msg.sender)


@external
def acceptAdmin():
    assert msg.sender == self.nextAdmin, "!next admin"
    self.admin = msg.sender
    self.nextAdmin = ZERO_ADDRESS
    log AcceptAdmin(msg.sender)


@external
def setTimeLock(timeLock: address):
    assert msg.sender == self.timeLock, "!time lock"
    assert timeLock != self.timeLock, "new time lock = current"
    self.timeLock = timeLock
    log SetTimeLock(timeLock)

# TODO: test migration
@external
def setVault(vault: address):
    assert msg.sender == self.timeLock, "!time lock"
    self.vault = Vault(vault)
