// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwapUsdp3Crv {
    function coins(uint _i) external view returns (address);

    function get_virtual_price() external view returns (uint);
}
