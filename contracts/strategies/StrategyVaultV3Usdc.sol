// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

import "./StrategyVaultV3.sol";

contract StrategyVaultV3Usdc is StrategyVaultV3 {
    constructor(
        address _fundManager,
        address _treasury
    )
        StrategyVaultV3(
            0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48,
            _fundManager,
            _treasury,
            IVaultV3(0x09DAb27cC3758040eea0f7b51df2Aee14bc003D6)
        )
    {}
}
