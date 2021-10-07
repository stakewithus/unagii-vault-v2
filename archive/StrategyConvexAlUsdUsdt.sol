// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexAlUsd.sol";

contract StrategyConvexAlUsdUsdt is StrategyConvexAlUsd {
    constructor(address _vault, address _treasury)
        StrategyConvexAlUsd(
            // USDT
            0xdAC17F958D2ee523a2206206994597C13D831ec7,
            _vault,
            _treasury,
            3
        )
    {}
}
