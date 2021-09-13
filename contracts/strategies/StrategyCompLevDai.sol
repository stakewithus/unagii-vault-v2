// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// version 1.0.0

import "./StrategyCompLev.sol";

contract StrategyCompLevDai is StrategyCompLev {
    constructor(
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    )
        StrategyCompLev(
            // DAI
            0x6B175474E89094C44Da98b954EedeAC495271d0F,
            _vault,
            _treasury,
            _minProfit,
            _maxProfit,
            // CDAI
            0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643
        )
    {}
}
