// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyConvexUsdp.sol";

contract StrategyConvexUsdpDai is StrategyConvexUsdp {
    constructor(
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    )
        StrategyConvexUsdp(
            0x6B175474E89094C44Da98b954EedeAC495271d0F,
            _vault,
            _treasury,
            _minProfit,
            _maxProfit,
            1
        )
    {}
}
