from brownie import TimeLock, accounts, network, web3
from brownie import ZERO_ADDRESS


def main():
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    gas_price = web3.eth.gas_price * 1.1
    print(f"gas price: {gas_price}")

    TimeLock.deploy({"from": account, "gas_price": gas_price})
