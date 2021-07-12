from brownie import Vault, accounts, network
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "TEST": {
            "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
            "uToken": "0x69c529Ec8e451D15c5EB394B3Edaca7304B7ff56",
        },
    },
    "mainnet": {
        "DAI": {
            "token": "0x6B175474E89094C44DA98B954EEDEAC495271D0F",
            "uToken": "0xffd51A24C65CC6981F3A543320fDadaf57ffFD7A",
        },
        "USDC": {
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "uToken": "0x8ae16964763Bab7D73c5ECEBe7A51E6827BaED66",
        },
        "USDT": {
            "token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "uToken": "",
        },
        "WBTC": {
            "token": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "uToken": "",
        },
    },
}


def deploy_ropsten_test_vault():
    deploy(config["ropsten"]["TEST"])


def deploy_mainnet_dai_vault():
    deploy(config["mainnet"]["DAI"])


def deploy_mainnet_usdc_vault():
    deploy(config["mainnet"]["USDC"])


def deploy_mainnet_usdt_vault():
    deploy(config["mainnet"]["USDT"])


def deploy_mainnet_wbtc_vault():
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

    Vault.deploy(
        args["token"], args["uToken"], guardian, ZERO_ADDRESS, {"from": account}
    )
