// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "./StrategyCompLev.sol";

contract StrategyCompLevDai is StrategyCompLev {
    constructor(address _fundManager, address _treasury)
        StrategyCompLev(
            0x6B175474E89094C44Da98b954EedeAC495271d0F,
            _fundManager,
            _treasury,
            0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643
        )
    {}
}
