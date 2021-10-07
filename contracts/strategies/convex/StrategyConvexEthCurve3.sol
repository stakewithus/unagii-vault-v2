// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: compiler version

// version 1.0.0

import "./StrategyConvexEth.sol";

uint constant N_TOKENS = 3;

contract StrategyConvexEthCurve3 is StrategyConvexEth {
    constructor(
        address _vault,
        address _treasury,
        address _booster,
        uint _pid,
        address _curve,
        address _lp,
        uint _index,
        address[] memory _rewards,
        address[] memory _dexes
    )
        StrategyConvexEth(
            _vault,
            _treasury,
            _booster,
            _pid,
            _curve,
            _lp,
            _index,
            _rewards,
            _dexes
        )
    {
        require(_index < N_TOKENS, "index >= N_TOKENS");
    }

    function _addLiquidity(uint _amount, uint _min) internal override {
        uint[N_TOKENS] memory amounts;
        amounts[INDEX] = _amount;
        CURVE.add_liquidity{value: _amount}(amounts, _min);
    }

    function _removeLiquidity(uint _shares, uint _min) internal override {
        CURVE.remove_liquidity_one_coin(_shares, int128(INDEX), _min);
    }
}
