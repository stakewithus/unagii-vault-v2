// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

struct PoolInfo {
    address lptoken;
    address token;
    address gauge;
    address crvRewards;
    address stash;
    bool shutdown;
}

interface Booster {
    function poolInfo(uint _pid) external view returns (PoolInfo calldata);

    function deposit(
        uint _pid,
        uint _amount,
        bool _stake
    ) external returns (bool);

    function withdraw(uint _pid, uint _amount) external returns (bool);
}
