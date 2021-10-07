// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 1.0.0
import "./convex/StrategyConvexCurveZap4.sol";

contract StrategyConvexUsdp is StrategyConvexCurveZap4 {
    address private constant _BOOSTER = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    uint private constant _PID = 28;

    address private constant _ZAP = 0x3c8cAee4E09296800f8D29A68Fa3837e2dae4940;
    address private constant _CURVE = 0x42d7025938bEc20B69cBae5A77421082407f053A;
    address private constant _CURVE_LP = 0x7Eb40E450b9655f4B3cC4259BCC731c63ff55ae6;

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
        StrategyConvexCurveZap4(
            _token,
            _vault,
            _treasury,
            _BOOSTER,
            _PID,
            _ZAP,
            _CURVE,
            _CURVE_LP,
            _index,
            _decimals,
            _REWARDS,
            _DEXES
        )
    {}
}
