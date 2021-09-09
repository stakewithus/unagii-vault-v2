// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/math/SafeMath.sol";

contract PerfFee {
    using SafeMath for uint;

    event SetMinMaxProfit(uint _minProfit, uint _maxProfit);

    // Performance fee
    uint private constant MAX_PERF_FEE = 2000;
    uint private constant MIN_PERF_FEE = 100;
    uint private constant PERF_FEE_DIFF = MAX_PERF_FEE - MIN_PERF_FEE;
    uint private constant PERF_FEE_DENOMINATOR = 10000;
    /*
    min and max profit are used to calculate performance fee
    */
    uint public minProfit;
    uint public maxProfit;

    /*
    @notice Set min and max profit
    @param _minProfit Minimum profit
    @param _maxProfit Maximum profit
    */
    function _setMinMaxProfit(uint _minProfit, uint _maxProfit) internal {
        require(_minProfit < _maxProfit, "min profit >= max profit");
        minProfit = _minProfit;
        maxProfit = _maxProfit;
        emit SetMinMaxProfit(_minProfit, _maxProfit);
    }

    /*
    @notice Calculate numerator of performance fee
    @param _profit Current profit
    @dev Returns current perf fee 
    @dev when profit <= minProfit, perf fee is MAX_PERF_FEE
         when profit >= maxProfit, perf fee is MIN_PERF_FEE
    */
    function _calcPerfFeeNumerator(uint _profit) internal view returns (uint) {
        /*
        y0 = max perf fee
        y1 = min perf fee
        x0 = min profit
        x1 = max profit

        x = current profit
        y = perf fee
          = (y1 - y0) / (x1 - x0) * (x - x0) + y0

        when x = x0, y = y0
             x = x1, y = y1
        */
        if (_profit <= minProfit) {
            return MAX_PERF_FEE;
        }
        if (_profit < maxProfit) {
            return
                MAX_PERF_FEE -
                ((PERF_FEE_DIFF.mul(_profit - minProfit)) / (maxProfit - minProfit));
        }
        return MIN_PERF_FEE;
    }

    /*
    @notice Calculate performance fee based on profit
    @param _profit Profit from harvest
    @dev Returns performance fee
    */
    function _calcPerfFee(uint _profit) internal view returns (uint fee) {
        fee = _profit.mul(_calcPerfFeeNumerator(_profit)) / PERF_FEE_DENOMINATOR;
    }

    function calcPerfFee(uint _profit) external view returns (uint) {
        return _calcPerfFee(_profit);
    }
}
