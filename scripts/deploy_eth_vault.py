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
            "uToken": "0xDe07f45688cb6CfAaC398c1485860e186D55996D",
        },
    },
}


def ropsten_eth():
    deploy(config["ropsten"]["ETH"])


def mainnet_eth():
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
    worker = account

    EthVault.deploy(args["uToken"], guardian, worker, {"from": account})
