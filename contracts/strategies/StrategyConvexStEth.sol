// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: compiler version

// version 1.0.0

import "./convex/StrategyConvexEthCurve2.sol";

contract StrategyConvexStEth is StrategyConvexEthCurve2 {
    address private constant _BOOSTER = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    uint private constant _PID = 25;

    address private constant _CURVE = 0xDC24316b9AE028F1497c275EB9192a3Ea0f67022;
    address private constant _CURVE_LP = 0x06325440D014e39736583c165C2963BA99fAf14E;
    uint private constant _INDEX = 0;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant LDO = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32;

    address[] private _REWARDS = [CRV, CVX, LDO];
    address[] private _DEXES = [SUSHISWAP, SUSHISWAP, SUSHISWAP];

    constructor(address _vault, address _treasury)
        StrategyConvexEthCurve2(
            _vault,
            _treasury,
            _BOOSTER,
            _PID,
            _CURVE,
            _CURVE_LP,
            _INDEX,
            _REWARDS,
            _DEXES
        )
    {}
}
