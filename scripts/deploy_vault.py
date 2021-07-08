from brownie import TestToken, accounts, network


def main():
    network_name = network.show_active()

    assert network_name == "ropsten"
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    TestToken.deploy("test", "TEST", 18, {"from": account})