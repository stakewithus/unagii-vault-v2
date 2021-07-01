// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

import "./StrategyConvexUsdp.sol";

contract StrategyConvexUsdpDai is StrategyConvexUsdp {
    constructor(address _fundManager, address _treasury)
        StrategyConvexUsdp(
            0x6B175474E89094C44Da98b954EedeAC495271d0F,
            _fundManager,
            _treasury,
            1
        )
    {}
}
