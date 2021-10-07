// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwapBbtc {
    /*
    0 bBTC
    1 renBTC
    2 wBTC
    3 sBTC
    */
    function get_virtual_price() external view returns (uint);

    function balances(uint index) external view returns (uint);
}
