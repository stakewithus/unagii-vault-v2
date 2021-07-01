// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

import "./StrategyConvexUsdp.sol";

contract StrategyConvexUsdpUsdt is StrategyConvexUsdp {
    constructor(address _fundManager, address _treasury)
        StrategyConvexUsdp(
            0xdAC17F958D2ee523a2206206994597C13D831ec7,
            _fundManager,
            _treasury,
            3
        )
    {}
}
