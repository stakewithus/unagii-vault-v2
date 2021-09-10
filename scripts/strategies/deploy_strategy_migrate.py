from brownie import StrategyMigrate, accounts, network, web3
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "TEST": {
            "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
            "fundManager": "0xe9558bC2fC2d8203bFC467Ab67f7016c90400549",
            "v2": "0x7905D4638DD6B23fcDFBE3e04fEBC911aD87Cde7",
            "v3": "0xD5198E50741FE6A513ce9940b78daa7f6766fB54",
        },
    },
}


def test():
    deploy(config["ropsten"]["TEST"])


def deploy(args):
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    treasury = account

    gas_price = web3.eth.gas_price * 1.2
    print("gas price:", gas_price)

    StrategyMigrate.deploy(
        args["token"],
        args["fundManager"],
        treasury,
        args["v2"],
        args["v3"],
        {"from": account, "gas_price": gas_price},
    )
