import brownie
import pytest


def test_flash_eth(chain, setup_eth, ethVault, flashEth, user):
    vault = ethVault
    flash = flashEth

    user.transfer(flash, 1000)

    with brownie.reverts():
        flash.deposit_and_withdraw()

    flash.deposit()

    with brownie.reverts():
        flash.withdraw_and_deposit()

    delay = vault.blockDelay()
    chain.mine(delay)

    # does not revert after delay
    flash.withdraw()