// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface IErc20FundManager {
    function token() external view returns (address);

    function borrow(uint amount) external returns (uint);

    function repay(uint amount) external returns (uint);

    function report(uint gain, uint loss) external returns (uint);

    function getDebt(address strategy) external view returns (uint);
}
