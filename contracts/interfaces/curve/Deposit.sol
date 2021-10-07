// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface Deposit {
    function token() external view returns (address);

    function add_liquidity(uint[2] calldata _amounts, uint _min_mint_amount) external;

    function add_liquidity(uint[3] calldata _amounts, uint _min_mint_amount) external;

    function add_liquidity(uint[4] calldata _amounts, uint _min_mint_amount) external;

    function remove_liquidity_one_coin(
        uint _burn_amount,
        int128 _i,
        uint _min_amount
    ) external;
}
