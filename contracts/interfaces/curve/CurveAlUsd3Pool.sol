// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface CurveAlUsd3Pool {
    // Curve.fi Factory USD Metapool v2
    function add_liquidity(
        address pool,
        uint[4] calldata amounts,
        uint min_mint_amount
    ) external returns (uint);
}
