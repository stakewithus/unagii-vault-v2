from brownie import (
    StrategyConvexBbtcWbtc,
    accounts,
    network,
)
from brownie import ZERO_ADDRESS

config = {
    "mainnet": {
        "WBTC": {
            "fundManager": "0xd5A84Cbb69351c6991BA56CF78052f59092d404C",
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
