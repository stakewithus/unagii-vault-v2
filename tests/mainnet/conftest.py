import pytest

from brownie import interface, FundManager, EthFundManager, ZERO_ADDRESS


@pytest.fixture(scope="session")
def admin(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def guardian(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def worker(accounts):
    yield accounts[2]


@pytest.fixture(scope="session")
def treasury(accounts):
    yield accounts[3]


@pytest.fixture(scope="session")
def eth_whale(accounts):
    yield accounts[-1]


@pytest.fixture(scope="session")
def daiFundManager(admin, guardian, worker, dai):
    fundManager = FundManager.deploy(
        dai, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="session")
def usdcFundManager(admin, guardian, worker, usdc):
    fundManager = FundManager.deploy(
        usdc, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="session")
def usdtFundManager(admin, guardian, worker, usdt):
    fundManager = FundManager.deploy(
        usdt, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="session")
def wbtcFundManager(admin, guardian, worker, wbtc):
    fundManager = FundManager.deploy(
        wbtc, guardian, worker, ZERO_ADDRESS, {"from": admin}
    )
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="session")
def ethFundManager(admin, guardian, worker):
    fundManager = EthFundManager.deploy(guardian, worker, ZERO_ADDRESS, {"from": admin})
    fundManager.initialize({"from": admin})
    yield fundManager


@pytest.fixture(scope="session")
def dai():
    yield interface.IERC20("0x6B175474E89094C44DA98B954EEDEAC495271D0F")


@pytest.fixture(scope="session")
def usdc():
    yield interface.IERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")


@pytest.fixture(scope="session")
def usdt():
    yield interface.IERC20("0xdAC17F958D2ee523a2206206994597C13D831ec7")


@pytest.fixture(scope="session")
def wbtc():
    yield interface.IERC20("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")


@pytest.fixture(scope="session")
def dai_whale(accounts):
    yield accounts.at("0xF977814e90dA44bFA03b6295A0616a897441aceC", force=True)


@pytest.fixture(scope="session")
def usdc_whale(accounts):
    yield accounts.at("0xcEe284F754E854890e311e3280b767F80797180d", force=True)


@pytest.fixture(scope="session")
def usdt_whale(accounts):
    yield accounts.at("0xF977814e90dA44bFA03b6295A0616a897441aceC", force=True)


@pytest.fixture(scope="session")
def wbtc_whale(accounts):
    yield accounts.at("0xF977814e90dA44bFA03b6295A0616a897441aceC", force=True)
