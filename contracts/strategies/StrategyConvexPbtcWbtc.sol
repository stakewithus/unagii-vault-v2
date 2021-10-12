// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexPbtc.sol";

contract StrategyConvexPbtcWbtc is StrategyConvexPbtc {
    constructor(address _fundManager, address _treasury)
        StrategyConvexPbtc(WBTC, _fundManager, _treasury, 1)
    {}
}
