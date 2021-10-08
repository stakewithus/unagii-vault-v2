// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexBbtc.sol";

contract StrategyConvexBbtcWbtc is StrategyConvexBbtc {
    constructor(address _vault, address _treasury)
        StrategyConvexBbtc(WBTC, _vault, _treasury, 2, 8)
    {}
}
