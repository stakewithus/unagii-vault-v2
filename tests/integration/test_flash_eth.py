import brownie


def test_flash(chain, setup_eth, ethVault, flashEth, eth_whale):
    vault = ethVault
    flash = flashEth
    eth_whale.transfer(flash, 1000)

    with brownie.reverts():
        flash.deposit_and_withdraw()

    flash.deposit()

    with brownie.reverts():
        flash.withdraw_and_deposit()

    delay = vault.blockDelay()
    chain.mine(delay)

    # does not revert after delay
    flash.withdraw()