// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface StableSwapAlUsd3Crv is IERC20 {
    function coins(uint _i) external view returns (address);

    function get_virtual_price() external view returns (uint);
}
