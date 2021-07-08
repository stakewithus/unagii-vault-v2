from brownie import StrategyTest, accounts, network

config = {
    "token": "0xfA4B8F893631814bF47E05a1a29d9d4365A90adD",
    "fundManager": "0xe9558bC2fC2d8203bFC467Ab67f7016c90400549",
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
        config["token"], config["fundManager"], treasury, {"from": account}
    )
