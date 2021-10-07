// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwap {
    function get_virtual_price() external view returns (uint);

    function add_liquidity(uint[2] memory amounts, uint min) external;

    function add_liquidity(uint[3] memory amounts, uint min) external;

    function add_liquidity(uint[4] memory amounts, uint min) external;

    function remove_liquidity_one_coin(
        uint amount,
        int128 index,
        uint min
    ) external;
}
