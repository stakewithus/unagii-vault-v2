// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface DepositBbtc {
    /*
    0 bBTC
    1 renBTC
    2 wBTC
    3 sBTC
    */
    function add_liquidity(uint[4] memory amounts, uint min) external returns (uint);

    function remove_liquidity_one_coin(
        uint amount,
        int128 index,
        uint min
    ) external returns (uint);
}
