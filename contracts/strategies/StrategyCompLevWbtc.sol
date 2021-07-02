// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyCompLev.sol";

contract StrategyCompLevWbtc is StrategyCompLev {
    constructor(address _fundManager, address _treasury)
        StrategyCompLev(
            0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599,
            _fundManager,
            _treasury,
            0xccF4429DB6322D5C611ee964527D42E5d685DD6a
        )
    {}
}
