# unagii-vault-v2

### Install

```shell
# install virtualenv
python3 -m pip install --user virtualenv
virtualenv -p python3 venv
source venv/bin/activate

# install vyper
pip install vyper==0.2.12
pip install eth-brownie
pip install black
pip install blackadder
pip install slither-analyzer

brownie pm install OpenZeppelin/openzeppelin-contracts@3.4.0

cp .env.sample .env

# npm
npm i
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
