from brownie import StrategyVaultV3Eth, accounts, network

config = {
    "fundManager": "0x9501B3a6DcE1Bbe6094356391F3992e08EE90E3a",
    "treasury": "0x1C064EA662365c09c8E87242791dAcbb90002605",
}

# 0xE34ACB02B28Ea377603095bc868fE93f85734965
def main():
    network_name = network.show_active()

    assert network_name == "mainnet"
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    StrategyVaultV3Eth.deploy(
        config["fundManager"], config["treasury"], {"from": account}
    )
