// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../base/Strategy.sol";

contract StrategyTest is Strategy {
    using SafeERC20 for IERC20;

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    ) Strategy(_token, _vault, _treasury, _minProfit, _maxProfit) {}

    function _totalAssets() internal view override returns (uint) {
        return token.balanceOf(address(this));
    }

    function _deposit() internal override {}

    function _withdraw(uint _amount) internal override returns (uint) {
        uint bal = token.balanceOf(address(this));
        if (bal < _amount) {
            return bal;
        }
        return _amount;
    }

    function harvest(uint) external override onlyAuthorized {}

    function sweep(address) external override {}
}
