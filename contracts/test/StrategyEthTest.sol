// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../base/StrategyEth.sol";

contract StrategyEthTest is StrategyEth {
    using SafeERC20 for IERC20;

    constructor(
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    ) StrategyEth(_vault, _treasury, _minProfit, _maxProfit) {}

    function _totalAssets() internal view override returns (uint) {
        return address(this).balance;
    }

    function _deposit() internal override {}

    function _withdraw(uint _amount) internal override {}

    function _harvest() internal override {}

    function sweep(address) external override {}

    // helper function
    function _burn_(uint amount) external {
        address(0).transfer(amount);
    }
}
