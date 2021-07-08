from brownie import UnagiiToken, accounts, network

config = {
    "ropsten": {
        "TEST": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    },
    "mainnet": {
        "DAI": "0x6B175474E89094C44DA98B954EEDEAC495271D0F",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    },
}


def deploy_ropsten_utest():
    deploy(config["ropsten"]["TEST"])


def deploy_ropsten_ueth():
    deploy(config["ropsten"]["ETH"])


def deploy_mainnet_udai():
    deploy(config["mainnet"]["DAI"])


def deploy_mainnet_uusdc():
    deploy(config["mainnet"]["USDC"])


def deploy_mainnet_uusdt():
    deploy(config["mainnet"]["USDT"])


def deploy_mainnet_uwbtc():
    deploy(config["mainnet"]["WBTC"])


def deploy_mainnet_ueth():
    deploy(config["mainnet"]["ETH"])


def deploy(token_addr):
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    UnagiiToken.deploy(token_addr, {"from": account})