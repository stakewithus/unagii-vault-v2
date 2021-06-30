// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../Strategy.sol";

// Test Strategy.sol
contract StrategyTest is Strategy {
    using SafeERC20 for IERC20;

    constructor(
        address _token,
        address _fundManager,
        address _treasury
    ) Strategy(_token, _fundManager, _treasury) {}

    function _totalAssets() internal view returns (uint) {
        return token.balanceOf(address(this));
    }

    function totalAssets() external view override returns (uint) {
        return _totalAssets();
    }

    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        uint borrowed = fundManager.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");
        emit Deposit(_amount, borrowed);
    }

    function withdraw(uint _amount) external override onlyFundManager returns (uint) {
        uint amount = _amount;
        uint bal = token.balanceOf(address(this));
        if (bal < amount) {
            amount = bal;
        }

        uint loss = 0;
        uint debt = fundManager.getDebt(address(this));
        uint total = _totalAssets();
        if (debt > total) {
            loss = debt - total;
        }

        token.safeTransfer(msg.sender, amount);

        emit Withdraw(_amount, amount, loss);

        return loss;
    }

    function repay(uint _amount, uint _min) external override onlyAuthorized {
        uint repaid = fundManager.repay(_amount);
        require(repaid >= _min, "repaid < min");
        emit Repay(_amount, repaid);
    }

    function claimRewards(uint) external override onlyAuthorized {
        emit ClaimRewards(0);
    }

    function skim() external override onlyAuthorized {
        uint total = _totalAssets();
        uint debt = fundManager.getDebt(address(this));
        emit Skim(total, debt, 0);
    }

    function report(uint _minTotal, uint _maxTotal) external override onlyAuthorized {
        uint total = _totalAssets();

        uint gain = 0;
        uint loss = 0;
        uint free = 0;
        uint debt = fundManager.getDebt(address(this));

        if (total > debt) {
            gain = total - debt;

            free = token.balanceOf(address(this));
            if (gain > free) {
                gain = free;
            }
        } else {
            loss = debt - total;
        }

        if (gain > 0 || loss > 0) {
            fundManager.report(gain, loss);
        }

        emit Report(gain, loss, free, total, debt);
    }

    function harvest(
        uint,
        uint,
        uint
    ) external override onlyAuthorized {}

    function migrate(address _strategy) external override onlyAuthorized {}

    function sweep(address _token) external override {}
}
