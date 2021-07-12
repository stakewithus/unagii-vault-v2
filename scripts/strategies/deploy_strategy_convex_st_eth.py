from brownie import (
    StrategyConvexStEth,
    accounts,
    network,
)
from brownie import ZERO_ADDRESS

config = {
    "mainnet": {
        "ETH": {
            "fundManager": "0x09f15F979Bf1b0CC8c8a19ed2E2feFF8EdE60e54",
        },
    },
}


def eth():
    deploy(StrategyConvexStEth, config["mainnet"]["ETH"])


def deploy(Strategy, args):
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    treasury = account

    Strategy.deploy(args["fundManager"], treasury, {"from": account})
