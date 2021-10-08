// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 1.0.0
import "./convex/StrategyConvexCurveFactoryZap4.sol";

address constant ALUSD = 0xBC6DA0FE9aD5f3b0d58160288917AA56653660E9;
address constant DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;
address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;

contract StrategyConvexAlUsd is StrategyConvexCurveFactoryZap4 {
    address private constant _BOOSTER = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    uint private constant _PID = 36;

    address private constant _ZAP = 0xA79828DF1850E8a3A3064576f380D90aECDD3359;
    address private constant _CURVE = 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c;
    address private constant _CURVE_LP = 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant ALCX = 0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF;

    address[] private _REWARDS = [CRV, CVX, ALCX];
    address[] private _DEXES = [SUSHISWAP, SUSHISWAP, SUSHISWAP];

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _index,
        uint _decimals
    )
        StrategyConvexCurveFactoryZap4(
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
