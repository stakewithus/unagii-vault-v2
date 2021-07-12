from brownie import (
    StrategyConvexUsdpDai,
    StrategyConvexUsdpUsdc,
    accounts,
    network,
)
from brownie import ZERO_ADDRESS

config = {
    "mainnet": {
        "DAI": {
            "fundManager": "0x8a90faDe80feadCDD595c4f3611eB1886c924b61",
        },
        "USDC": {
            "fundManager": "0xf01c9a51ff69fC2982156be9D558d56002328Fcc",
        },
    },
}


def dai():
    deploy(StrategyConvexUsdpDai, config["mainnet"]["DAI"])


def usdc():
    deploy(StrategyConvexUsdpUsdc, config["mainnet"]["USDC"])


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
