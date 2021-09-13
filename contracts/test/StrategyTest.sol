// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../base/Strategy.sol";

interface ITestToken {
    function mint(address to, uint amount) external;
}

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

    function _withdraw(uint _amount) internal override {}

    function _harvest() internal override {
        ITestToken(address(token)).mint(address(this), 1e18);
    }

    function sweep(address) external override {}
}
