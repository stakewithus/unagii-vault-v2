// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./V2Strategy.sol";

contract V2StrategyTest is V2Strategy {
    using SafeERC20 for IERC20;

    constructor(
        address _token,
        address _fundManager,
        address _treasury
    ) V2Strategy(_token, _fundManager, _treasury) {}

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

    function _claimRewards(uint) internal {
        emit ClaimRewards(0);
    }

    function claimRewards(uint _minProfit) external override onlyAuthorized {
        _claimRewards(_minProfit);
    }

    function _skim() internal {
        uint total = _totalAssets();
        uint debt = fundManager.getDebt(address(this));
        emit Skim(total, debt, 0);
    }

    function skim() external override onlyAuthorized {
        _skim();
    }

    function _report(uint, uint) internal {
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

    function report(uint _minTotal, uint _maxTotal) external override onlyAuthorized {
        _report(_minTotal, _maxTotal);
    }

    function harvest(
        uint _minProfit,
        uint _minTotal,
        uint _maxTotal
    ) external override onlyAuthorized {
        _claimRewards(_minProfit);
        _skim();
        _report(_minTotal, _maxTotal);
    }

    function migrate(address _strategy) external override onlyAuthorized {
        token.transfer(_strategy, token.balanceOf(address(this)));
    }

    function sweep(address _token) external override {}
}
