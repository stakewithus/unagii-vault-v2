from brownie import (
    StrategyConvexBbtcWbtc,
    accounts,
    network,
)
from brownie import ZERO_ADDRESS

config = {
    "mainnet": {
        "WBTC": {
            "fundManager": "0x0349Cf57BaE5C0d9be56b9C478Ea3797c7BcFddB",
        },
    },
}


def wbtc():
    deploy(StrategyConvexBbtcWbtc, config["mainnet"]["WBTC"])


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
