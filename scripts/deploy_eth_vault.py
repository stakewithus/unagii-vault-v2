from brownie import EthVault, accounts, network
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "ETH": {
            "uToken": "0xDdC33E10f60EeC345440Dd49497b1dA38040bd54",
        },
    },
    "mainnet": {
        "ETH": {
            "uToken": "0x5a6170496aAEC8649B25ec0cd53e55bC38525B00",
        },
    },
}


def deploy_ropsten_eth_vault():
    deploy(config["ropsten"]["ETH"])


def deploy_mainnet_eth_vault():
    deploy(config["mainnet"]["ETH"])


def deploy(args):
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    guardian = account

    EthVault.deploy(args["uToken"], guardian, ZERO_ADDRESS, {"from": account})
