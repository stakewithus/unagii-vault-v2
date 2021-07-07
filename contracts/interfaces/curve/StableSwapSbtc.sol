// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwapSbtc {
    /*
    0 renBTC
    1 wBTC
    2 sBTC
    */
    function add_liquidity(uint[3] memory amounts, uint min) external;

    function remove_liquidity_one_coin(
        uint amount,
        int128 index,
        uint min
    ) external;

    function get_virtual_price() external view returns (uint);
}
