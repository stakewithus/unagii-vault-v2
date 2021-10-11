// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface StableSwapMim3Crv {
    function get_virtual_price() external view returns (uint);
}
