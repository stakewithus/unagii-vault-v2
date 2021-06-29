// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

interface BaseRewardPool {
    function balanceOf(address _account) external view returns (uint);

    function getReward(address _account, bool _claimExtras) external returns (bool);

    function withdrawAndUnwrap(uint amount, bool claim) external returns (bool);
}
