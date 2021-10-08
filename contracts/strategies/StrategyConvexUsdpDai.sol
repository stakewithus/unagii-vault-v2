// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexUsdp.sol";

contract StrategyConvexUsdpDai is StrategyConvexUsdp {
    constructor(address _vault, address _treasury)
        StrategyConvexUsdp(DAI, _vault, _treasury, 1, 18)
    {}
}
