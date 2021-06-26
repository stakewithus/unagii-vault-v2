// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

interface CErc20 {
    function mint(uint mintAmount) external returns (uint);

    function redeemUnderlying(uint redeemAmount) external returns (uint);

    function borrow(uint borrowAmount) external returns (uint);

    function repayBorrow(uint repayAmount) external returns (uint);

    function redeem(uint) external returns (uint);

    function borrowBalanceCurrent(address account) external returns (uint);

    function balanceOfUnderlying(address account) external returns (uint);

    function getAccountSnapshot(address account)
        external
        view
        returns (
            uint,
            uint,
            uint,
            uint
        );
}
