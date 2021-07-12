from brownie import StrategyEthTest, accounts, network, web3

config = {
    "fundManager": "0x9Fb96bc1F352F26c0f624556ED39B65fa0a6Ac69",
}


def main():
    network_name = network.show_active()

    assert network_name == "ropsten"
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    treasury = account

    gas_price = web3.eth.gas_price
    print(f"gas price: {gas_price}")

    StrategyEthTest.deploy(
        config["fundManager"], treasury, {"from": account, "gas_price": gas_price}
    )
