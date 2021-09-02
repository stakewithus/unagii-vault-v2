// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 1.0.0

import "@openzeppelin/contracts/math/SafeMath.sol";

// TODO: test
contract PerfFee {
    using SafeMath for uint;

    event SetMinMaxTvl(uint _minTvl, uint _maxTvl);

    // Performance fee sent to treasury
    uint private constant MAX_PERF_FEE = 2000;
    uint private constant MIN_PERF_FEE = 100;
    uint private constant PERF_FEE_DIFF = MAX_PERF_FEE - MIN_PERF_FEE;
    uint private constant PERF_FEE_DENOMINATOR = 10000;
    /*
    tvl = total value locked in this contract
    min and max tvl are used to calculate performance fee
    */
    uint public minTvl;
    uint public maxTvl;

    /*
    @notice Set min and max TVL
    @param _minTvl Minimum TVL
    @param _maxTvl Maximum TVL
    */
    function _setMinMaxTvl(uint _minTvl, uint _maxTvl) internal {
        require(_minTvl < _maxTvl, "min tvl >= max tvl");
        minTvl = _minTvl;
        maxTvl = _maxTvl;
        emit SetMinMaxTvl(_minTvl, _maxTvl);
    }

    /*
    @notice Calculate performance fee based on total locked value
    @param _tvl Current total locked value in this contract
    @dev Returns current perf fee 
    @dev when tvl <= minTvl, perf fee is MAX_PERF_FEE
         when tvl >= maxTvl, perf fee is MIN_PERF_FEE
    */
    function _calcPerfFee(uint _tvl) internal view returns (uint) {
        /*
        y0 = max perf fee
        y1 = min perf fee
        x0 = min tvl
        x1 = max tvl

        x = current tvl
        y = perf fee
          = (y1 - y0) / (x1 - x0) * (x - x0) + y0

        when x = x0, y = y0
             x = x1, y = y1
        */
        if (_tvl <= minTvl) {
            return MAX_PERF_FEE;
        }
        if (_tvl < maxTvl) {
            return
                MAX_PERF_FEE - ((PERF_FEE_DIFF.mul(_tvl - minTvl)) / (maxTvl - minTvl));
        }
        return MIN_PERF_FEE;
    }

    function calcPerfFee(uint _tvl) external view returns (uint) {
        return _calcPerfFee(_tvl);
    }

    /*
    @notice Calculate fee based on profit and TVL
    @param _tvl Total value locked in this contract
    @param _profit Profit from harvest
    @dev Returns fee
    */
    function _calcFee(uint _tvl, uint _profit) internal view returns (uint fee) {
        fee = _profit.mul(_calcPerfFee(_tvl)) / PERF_FEE_DENOMINATOR;
    }
}
