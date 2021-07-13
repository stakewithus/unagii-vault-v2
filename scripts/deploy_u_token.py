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


def utest():
    deploy(config["ropsten"]["TEST"])


def ropsten_ueth():
    deploy(config["ropsten"]["ETH"])


def udai():
    deploy(config["mainnet"]["DAI"])


def uusdc():
    deploy(config["mainnet"]["USDC"])


def uusdt():
    deploy(config["mainnet"]["USDT"])


def uwbtc():
    deploy(config["mainnet"]["WBTC"])


def mainnet_ueth():
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