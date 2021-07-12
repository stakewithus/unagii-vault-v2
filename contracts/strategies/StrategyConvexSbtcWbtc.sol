// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexSbtc.sol";

contract StrategyConvexSbtcWbtc is StrategyConvexSbtc {
    constructor(address _fundManager, address _treasury)
        StrategyConvexSbtc(
            0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599,
            _fundManager,
            _treasury,
            1
        )
    {}
}
