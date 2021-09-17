from brownie import StrategyEthTest, accounts, network, web3

config = {
    "vault": "0x3A8cdb9f05912865eedC31A2114a5195fE3b7A28",
    "minProfit": 10 ** 18,
    "maxProfit": 100 * 10 ** 18,
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
        config["vault"],
        treasury,
        config["minProfit"],
        config["maxProfit"],
        {"from": account, "gas_price": gas_price},
    )
