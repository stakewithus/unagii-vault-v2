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

cp .env.sample .env
```

```shell
# black format python
black --check --include "(tests|scripts)" .
```
