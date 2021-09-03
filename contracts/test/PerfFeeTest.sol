// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../base/PerfFee.sol";

contract PerfFeeTest is PerfFee {
    function setMinMaxProfit(uint _minProfit, uint _maxProfit) external {
        _setMinMaxProfit(_minProfit, _maxProfit);
    }

    function calcFee(uint _profit) external view returns (uint) {
        return _calcFee(_profit);
    }
}
