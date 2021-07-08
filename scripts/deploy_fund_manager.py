from brownie import FundManager, accounts, network
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "TEST": {
            "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
        },
    },
    "mainnet": {
        "DAI": {
            "token": "0x6B175474E89094C44DA98B954EEDEAC495271D0F",
        },
        "USDC": {
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        },
        "USDT": {
            "token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        },
        "WBTC": {
            "token": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        },
    },
}


def deploy_ropsten_test_fund_manager():
    deploy(config["ropsten"]["TEST"])


def deploy_mainnet_dai_fund_manager():
    deploy(config["mainnet"]["DAI"])


def deploy_mainnet_usdc_fund_manager():
    deploy(config["mainnet"]["USDC"])


def deploy_mainnet_usdt_fund_manager():
    deploy(config["mainnet"]["USDT"])


def deploy_mainnet_wbtc_fund_manager():
    deploy(config["mainnet"]["WBTC"])


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

    FundManager.deploy(args["token"], guardian, worker, ZERO_ADDRESS, {"from": account})
