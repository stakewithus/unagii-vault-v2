// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexAlUsd.sol";

contract StrategyConvexAlUsdUsdt is StrategyConvexAlUsd {
    constructor(address _vault, address _treasury)
        StrategyConvexAlUsd(USDT, _vault, _treasury, 3, 6)
    {}
}
