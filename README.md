# unagii-vault-v2

![unagii-v2](./doc/unagii-v2.png)

### Install

```shell
# install virtualenv
python3 -m pip install --user virtualenv
virtualenv -p python3 venv
source venv/bin/activate

# install vyper
pip install vyper==0.2.12
pip install eth-brownie
pip install eth_account
pip install black
pip install blackadder
pip install slither-analyzer

brownie pm install OpenZeppelin/openzeppelin-contracts@3.4.0

cp .env.sample .env

# npm
npm i
```

### Test

```shell
brownie test tests/path-to-test-file-or-folder
```

### Mainnet Test

```shell
source .env

ganache-cli \
--fork https://mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID \
--unlock $DAI_WHALE \
--unlock $USDC_WHALE \
--unlock $USDT_WHALE \
--unlock $WBTC_WHALE \
--networkId 999

env $(cat .env) brownie test tests/mainnet/test.py --network mainnet-fork -s

```

```shell
# black format python
black --check --include "(tests|scripts)" .
# format vyper
blackadder --fast --include '\.vy$' contracts

# select solc compiler
solc-select install 0.8.4
solc-select use 0.8.4

# slither
slither contracts/Contract.sol
```

### Deploy

```shell
brownie accounts new dev

env $(cat .env) brownie run scripts/deploy_test_token.py --network ropsten
env $(cat .env) brownie run scripts/deploy_u_token.py deploy_ropsten_utest --network ropsten
env $(cat .env) brownie run scripts/deploy_vault.py deploy_ropsten_test_vault --network ropsten
env $(cat .env) brownie run scripts/deploy_eth_vault.py deploy_ropsten_eth_vault --network ropsten

```

```shell
# ropsten
# TestToken
0xfA4B8F893631814bF47E05a1a29d9d4365A90adD

# uTEST
0x69c529Ec8e451D15c5EB394B3Edaca7304B7ff56
# uETH
0xDdC33E10f60EeC345440Dd49497b1dA38040bd54

# TEST Vault
0x7905D4638DD6B23fcDFBE3e04fEBC911aD87Cde7
# ETH Vault
0xFaEeE4847AEE7a7eC48eb1BB3103E84FB7b4a0D1

# mainnet
```
