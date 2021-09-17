from brownie import StrategyMigrateEth, accounts, network, web3
from brownie import ZERO_ADDRESS

config = {
    "ropsten": {
        "ETH": {
            "ethFundManager": "0x9Fb96bc1F352F26c0f624556ED39B65fa0a6Ac69",
            "v2": "0xFaEeE4847AEE7a7eC48eb1BB3103E84FB7b4a0D1",
            "v3": "0x3A8cdb9f05912865eedC31A2114a5195fE3b7A28",
        },
    },
}


def ropsten_eth():
    deploy(config["ropsten"]["ETH"])


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

    StrategyMigrateEth.deploy(
        args["ethFundManager"],
        treasury,
        args["v2"],
        args["v3"],
        {"from": account, "gas_price": gas_price},
    )
