// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwapREth {
    function get_virtual_price() external view returns (uint);

    function add_liquidity(uint[2] memory amounts, uint min) external payable;

    function remove_liquidity_one_coin(
        uint _token_amount,
        int128 i,
        uint min_amount
    ) external;
}
