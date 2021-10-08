// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 1.0.0
import "./convex/StrategyConvexCurve3.sol";

address constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;

contract StrategyConvexSbtc is StrategyConvexCurve3 {
    address private constant _BOOSTER = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    uint private constant _PID = 7;

    address private constant _CURVE = 0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714;
    address private constant _CURVE_LP = 0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;

    address[] private _REWARDS = [CRV, CVX];
    address[] private _DEXES = [SUSHISWAP, SUSHISWAP];

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _index,
        uint _decimals
    )
        StrategyConvexCurve3(
            _token,
            _vault,
            _treasury,
            _BOOSTER,
            _PID,
            _CURVE,
            _CURVE_LP,
            _index,
            _decimals,
            _REWARDS,
            _DEXES
        )
    {}
}
