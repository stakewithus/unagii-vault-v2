from brownie import Vault, accounts, network
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "TEST": {
            "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
            # "uToken": "0x69c529Ec8e451D15c5EB394B3Edaca7304B7ff56",
            "uToken": "0xE241795cacaF3083Aee8054E2F34520b1e3A0940",
        },
    },
    "mainnet": {
        "DAI": {
            "token": "0x6B175474E89094C44DA98B954EEDEAC495271D0F",
            "uToken": "0x634b0273D7060313FAA60f96705116c9DE50fA1f",
        },
        "USDC": {
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "uToken": "0x49b09e7E434a3A4A924A3b640cBBA54bF93B5677",
        },
        "USDT": {
            "token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "uToken": "0xBF8734c5A7b3e6D88aa0110beBB37844AC043d0A",
        },
        "WBTC": {
            "token": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "uToken": "0x7F20551E082ba3E035F2890cBD1EC4E275b9C8C0",
        },
    },
}


def test():
    deploy(config["ropsten"]["TEST"])


def dai():
    deploy(config["mainnet"]["DAI"])


def usdc():
    deploy(config["mainnet"]["USDC"])


def usdt():
    deploy(config["mainnet"]["USDT"])


def wbtc():
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

    Vault.deploy(args["token"], args["uToken"], guardian, worker, {"from": account})
