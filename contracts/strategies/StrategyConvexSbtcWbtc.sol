// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexSbtc.sol";

contract StrategyConvexSbtcWbtc is StrategyConvexSbtc {
    constructor(address _vault, address _treasury)
        StrategyConvexSbtc(WBTC, _vault, _treasury, 1, 8)
    {}
}
