// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 1.0.0
import "./convex/StrategyConvexCurveZap4.sol";

contract StrategyConvexObtc is StrategyConvexCurveZap4 {
    address private constant _BOOSTER = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31;
    uint private constant _PID = 20;

    address private constant _ZAP = 0xd5BCf53e2C81e1991570f33Fa881c49EEa570C8D;
    address private constant _CURVE = 0xd81dA8D904b52208541Bade1bD6595D8a251F8dd;
    address private constant _CURVE_LP = 0x2fE94ea3d5d4a175184081439753DE15AeF9d614;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant BOR = 0x3c9d6c1C73b31c837832c72E04D3152f051fc1A9;

    address[] private _REWARDS = [CRV, CVX, BOR];
    address[] private _DEXES = [SUSHISWAP, SUSHISWAP, SUSHISWAP];

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
