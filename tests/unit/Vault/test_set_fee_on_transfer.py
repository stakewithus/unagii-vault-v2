import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def setup(module_isolation):
    pass


def test_set_fee_on_transfer(accounts, vault, admin):
    # not admin
    with brownie.reverts("!admin"):
        vault.setFeeOnTransfer(True, {"from": accounts[1]})

    # admin can call
    vault.setFeeOnTransfer(True, {"from": admin})
    assert vault.feeOnTransfer()
