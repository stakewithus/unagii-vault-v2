// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// TODO: solidity version

interface IVault {
    function token() external view returns (address);

    function borrow(uint amount) external returns (uint);

    function repay(uint amount) external returns (uint);
}
