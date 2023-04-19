from brownie import StrategyVaultV3Usdc, accounts, network

config = {
    "fundManager": "0xb00AA15F78A278Be2FCb2aa7de899F3F863780f8",
    "treasury": "0x1C064EA662365c09c8E87242791dAcbb90002605",
}

# 0x53B942004Ad80D15a49434215681949BBD6C71c1
def main():
    network_name = network.show_active()

    assert network_name == "mainnet"
    print(f"network: {network_name}")

    account = accounts.load("dev")
    bal = account.balance()
    print("Account:", account)
    print("ETH balance:", bal)
    print("-------------------")

    StrategyVaultV3Usdc.deploy(
        config["fundManager"], config["treasury"], {"from": account}
    )
