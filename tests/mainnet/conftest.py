import os
import pytest

from brownie import interface, Vault, UnagiiToken, ZERO_ADDRESS


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
def uDai(dai, admin):
    uToken = UnagiiToken.deploy(dai, {"from": admin})
    yield uToken


@pytest.fixture(scope="session")
def daiVault(dai, uDai, admin, guardian, worker):
    vault = Vault.deploy(dai, uDai, guardian, worker, {"from": admin})
    uDai.setMinter(vault, {"from": admin})
    vault.setPause(False)
    yield vault


@pytest.fixture(scope="session")
def uUsdc(usdc, admin):
    uToken = UnagiiToken.deploy(usdc, {"from": admin})
    yield uToken


@pytest.fixture(scope="session")
def usdcVault(usdc, uUsdc, admin, guardian, worker):
    vault = Vault.deploy(usdc, uUsdc, guardian, worker, {"from": admin})
    uUsdc.setMinter(vault, {"from": admin})
    vault.setPause(False)
    yield vault


@pytest.fixture(scope="session")
def uUsdt(usdt, admin):
    uToken = UnagiiToken.deploy(usdt, {"from": admin})
    yield uToken


@pytest.fixture(scope="session")
def usdtVault(usdt, uUsdt, admin, guardian, worker):
    vault = Vault.deploy(usdt, uUsdt, guardian, worker, {"from": admin})
    uUsdt.setMinter(vault, {"from": admin})
    vault.setPause(False)
    yield vault


@pytest.fixture(scope="session")
def uWbtc(wbtc, admin):
    uToken = UnagiiToken.deploy(wbtc, {"from": admin})
    yield uToken


@pytest.fixture(scope="session")
def wbtcVault(wbtc, uWbtc, admin, guardian, worker):
    vault = Vault.deploy(wbtc, uWbtc, guardian, worker, {"from": admin})
    uWbtc.setMinter(vault, {"from": admin})
    vault.setPause(False)
    yield vault


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
    yield accounts.at(os.getenv("DAI_WHALE"), force=True)


@pytest.fixture(scope="session")
def usdc_whale(accounts):
    yield accounts.at(os.getenv("USDC_WHALE"), force=True)


@pytest.fixture(scope="session")
def usdt_whale(accounts):
    yield accounts.at(os.getenv("USDT_WHALE"), force=True)


@pytest.fixture(scope="session")
def wbtc_whale(accounts):
    yield accounts.at(os.getenv("WBTC_WHALE"), force=True)
