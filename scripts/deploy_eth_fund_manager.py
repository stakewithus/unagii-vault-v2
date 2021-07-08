from brownie import EthFundManager, accounts, network
from brownie import ZERO_ADDRESS


def main():
    network_name = network.show_active()
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    guardian = account
    worker = account

    EthFundManager.deploy(guardian, worker, ZERO_ADDRESS, {"from": account})
