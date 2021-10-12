// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexMim.sol";

contract StrategyConvexMimUsdt is StrategyConvexMim {
    constructor(address _fundManager, address _treasury)
        StrategyConvexMim(USDT, _fundManager, _treasury, 3)
    {}
}
