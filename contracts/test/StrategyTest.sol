// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../Strategy.sol";

contract StrategyTest is Strategy {
    using SafeERC20 for IERC20;

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    ) Strategy(_token, _vault, _treasury, _minProfit, _maxProfit) {}

    function _totalAssets() internal view returns (uint) {
        return token.balanceOf(address(this));
    }

    function totalAssets() external view override returns (uint) {
        return _totalAssets();
    }

    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        uint borrowed = vault.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");
    }

    function withdraw(uint _amount) external override onlyVault {
        uint amount = _amount;
        uint bal = token.balanceOf(address(this));
        if (bal < amount) {
            amount = bal;
        }
        token.safeTransfer(msg.sender, amount);
    }

    function repay(uint _amount, uint _min) external override onlyAuthorized {
        uint repaid = vault.repay(_amount);
        require(repaid >= _min, "repaid < min");
    }

    function harvest(uint) external override onlyAuthorized {}

    function migrate(address _strategy) external override onlyVault {
        token.transfer(_strategy, token.balanceOf(address(this)));
    }

    function sweep(address) external override {}
}
