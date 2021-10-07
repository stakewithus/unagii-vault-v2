// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyCompLev.sol";

contract StrategyCompLevUsdc is StrategyCompLev {
    constructor(address _vault, address _treasury)
        StrategyCompLev(
            // USDC
            0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48,
            _vault,
            _treasury,
            // CUSDC
            0x39AA39c021dfbaE8faC545936693aC917d5E7563
        )
    {}
}
