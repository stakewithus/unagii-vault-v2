// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// https://github.com/curvefi/curve-factory/blob/master/contracts/DepositZapUSD.vy
interface DepositZapAlUsd3Crv {
    // Curve.fi Factory USD Metapool v2
    function add_liquidity(
        address _pool,
        uint[4] calldata _amounts,
        uint _min_mint_amount
    ) external returns (uint);

    function remove_liquidity_one_coin(
        address _pool,
        uint _burn_amount,
        int128 _i,
        uint _min_amount
    ) external returns (uint);
}
