// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: compiler version

// version 1.0.0

import "../../interfaces/curve/Deposit.sol";
import "./StrategyConvex.sol";

uint constant N_TOKENS = 4;

contract StrategyConvexCurveZap4 is StrategyConvex {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    Deposit private immutable ZAP;

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit,
        address _booster,
        uint _pid,
        address _zap,
        address _curve,
        uint _index,
        uint _decimals,
        address[] memory _rewards,
        address[] memory _dexes
    )
        StrategyConvex(
            _token,
            _vault,
            _treasury,
            _minProfit,
            _maxProfit,
            _booster,
            _pid,
            _curve,
            _index,
            _decimals,
            _rewards,
            _dexes
        )
    {
        require(_index < N_TOKENS, "index >= N_TOKENS");

        ZAP = Deposit(_zap);

        // allow token deposit into curve
        IERC20(_token).safeApprove(_zap, type(uint).max);
        // allow withdraw from curve
        address lp = Deposit(_zap).token();
        IERC20(lp).safeApprove(_zap, type(uint).max);
    }

    function _addLiquidity(uint _amount, uint _min) internal override {
        // uint[N_TOKENS] memory amounts;
        // amounts[INDEX] = _amount;
        // CURVE.add_liquidity(amounts, _min);
    }

    function _removeLiquidity(uint _shares, uint _min) internal override {
        // CURVE.remove_liquidity_one_coin(_shares, int128(INDEX), _min);
    }
}
