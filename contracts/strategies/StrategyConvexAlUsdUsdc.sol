// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexAlUsd.sol";

contract StrategyConvexAlUsdUsdc is StrategyConvexAlUsd {
    constructor(
        address _vault,
        address _treasury,
        uint _minTvl,
        uint _maxTvl
    )
        StrategyConvexAlUsd(
            0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48,
            _vault,
            _treasury,
            _minTvl,
            _maxTvl,
            2
        )
    {}
}
