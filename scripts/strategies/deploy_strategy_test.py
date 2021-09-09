from brownie import StrategyTest, accounts, network

config = {
    "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
    "vault": "0x2FD1Ec28fbb5392c5488F417883f4992D54e4f98",
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

    StrategyTest.deploy(
        config["token"],
        config["vault"],
        treasury,
        config["minProfit"],
        config["maxProfit"],
        {"from": account},
    )
