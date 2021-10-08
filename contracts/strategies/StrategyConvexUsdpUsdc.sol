// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexUsdp.sol";

contract StrategyConvexUsdpUsdc is StrategyConvexUsdp {
    constructor(address _vault, address _treasury)
        StrategyConvexUsdp(USDC, _vault, _treasury, 2, 6)
    {}
}
