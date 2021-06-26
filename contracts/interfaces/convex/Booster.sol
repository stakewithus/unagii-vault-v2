// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface Booster {
    function deposit(
        uint _pid,
        uint _amount,
        bool _stake
    ) external returns (bool);

    function withdraw(uint _pid, uint _amount) external returns (bool);
}
