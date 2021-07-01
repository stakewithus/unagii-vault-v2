// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface DepositZapUsdp3Crv {
    function add_liquidity(uint[4] calldata _amounts, uint _min_mint_amount)
        external
        returns (uint);

    function remove_liquidity_one_coin(
        uint _burn_amount,
        int128 _i,
        uint _min_amount
    ) external returns (uint);

    function calc_withdraw_one_coin(
        address _pool,
        uint _amount,
        int128 _i
    ) external view returns (uint);
}
