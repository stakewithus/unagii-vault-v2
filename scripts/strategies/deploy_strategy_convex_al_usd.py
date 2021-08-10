from brownie import (
    StrategyConvexAlUsdDai,
    StrategyConvexAlUsdUsdc,
    StrategyConvexAlUsdUsdt,
    accounts,
    network,
)
from brownie import ZERO_ADDRESS

config = {
    "mainnet": {
        "DAI": {
            "fundManager": "0x7C765C474D231fd915dc78832b478F309071cba7",
        },
        "USDC": {
            "fundManager": "0xb00AA15F78A278Be2FCb2aa7de899F3F863780f8",
        },
        "USDT": {
            "fundManager": "0xdF60b2CC40AFd588Bf650977A2d6C6AF39939f4C",
        },
    },
}


def dai():
    deploy(StrategyConvexAlUsdDai, config["mainnet"]["DAI"])


def usdc():
    deploy(StrategyConvexAlUsdUsdc, config["mainnet"]["USDC"])


def usdt():
    deploy(StrategyConvexAlUsdUsdt, config["mainnet"]["USDT"])


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
