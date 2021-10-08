// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexObtc.sol";

contract StrategyConvexObtcWbtc is StrategyConvexObtc {
    constructor(address _vault, address _treasury)
        StrategyConvexObtc(WBTC, _vault, _treasury, 2, 8)
    {}
}
