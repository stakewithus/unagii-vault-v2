// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: compiler version

// version 1.0.0
import "../../interfaces/convex/BaseRewardPool.sol";
import "../../interfaces/convex/Booster.sol";
import "../../interfaces/curve/StableSwap.sol";
import "../../base/StrategyEth.sol";

abstract contract StrategyConvexEth is StrategyEth {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    struct Reward {
        address addr;
        address dex;
        bool disabled;
    }

    Reward[] public rewards;

    // Convex //
    Booster private immutable BOOSTER;
    BaseRewardPool private immutable BASE_REWARD_POOL;
    uint private immutable PID;
    bool public shouldClaimExtras = true;

    // Curve //
    StableSwap internal immutable CURVE;
    IERC20 private immutable CURVE_LP;

    // prevent slippage from deposit / withdraw
    uint public slip = 100;
    uint private constant SLIP_MAX = 10000;

    uint internal immutable INDEX; // index of ETH

    constructor(
        address _vault,
        address _treasury,
        address _booster,
        uint _pid,
        address _curve,
        address _lp,
        uint _index,
        address[] memory _rewards,
        address[] memory _dexes
    ) StrategyEth(_vault, _treasury) {
        (address lp, , , address baseReward, , bool shutdown) = Booster(_booster)
        .poolInfo(_pid);
        require(!shutdown, "booster shut down");
        require(lp == _lp, "curve lp != booster lp");

        BOOSTER = Booster(_booster);
        PID = _pid;
        BASE_REWARD_POOL = BaseRewardPool(baseReward);

        CURVE = StableSwap(_curve);
        CURVE_LP = IERC20(_lp);

        INDEX = _index;

        // deposit into booster
        IERC20(lp).safeApprove(_booster, type(uint).max);

        // setup rewards
        require(_rewards.length == _dexes.length, "rewards.length != dexes.length");

        for (uint i = 0; i < _rewards.length; i++) {
            address _reward = _rewards[i];
            address dex = _dexes[i];
            require(_reward != address(0), "reward = zero address");
            require(dex != address(0), "dex = zero address");

            rewards.push(Reward({addr: _reward, dex: dex, disabled: false}));

            // approve new dex
            IERC20(_reward).safeApprove(dex, type(uint).max);
        }
    }

    function setDex(uint _i, address _dex) external onlyTimeLock {
        require(_dex != address(0), "dex = 0 address");

        Reward storage reward = rewards[_i];

        // disapprove current dex
        if (reward.dex != address(0)) {
            IERC20(reward.addr).safeApprove(reward.dex, 0);
        }

        reward.dex = _dex;

        // approve new dex
        IERC20(reward.addr).safeApprove(_dex, type(uint).max);
    }

    function setDisableReward(uint _i, bool _disabled) external onlyTimeLockOrAdmin {
        Reward storage reward = rewards[_i];
        require(reward.disabled != _disabled, "no change");
        rewards[_i].disabled = _disabled;
    }

    /*
    @notice Set max slippage for deposit and withdraw from Curve pool
    @param _slip Max amount of slippage allowed
    */
    function setSlip(uint _slip) external onlyAuthorized {
        require(_slip <= SLIP_MAX, "slip > max");
        slip = _slip;
    }

    // @dev Claim extra rewards (ALCX) from Convex
    function setShouldClaimExtras(bool _shouldClaimExtras) external onlyAuthorized {
        shouldClaimExtras = _shouldClaimExtras;
    }

    function _totalAssets() internal view override returns (uint total) {
        // amount of Curve LP tokens in Convex
        uint lpBal = BASE_REWARD_POOL.balanceOf(address(this));
        total = lpBal.mul(CURVE.get_virtual_price()) / 1e18;
        total = total.add(address(this).balance);
    }

    function _addLiquidity(uint _amount, uint _min) internal virtual;

    function _deposit() internal override {
        uint bal = address(this).balance;
        if (bal > 0) {
            /*
            shares = ETH amount * 1e18 / price per share
            */
            uint pricePerShare = CURVE.get_virtual_price();
            uint shares = bal.mul(1e18).div(pricePerShare);
            uint min = shares.mul(SLIP_MAX - slip) / SLIP_MAX;

            _addLiquidity(bal, min);
        }

        uint lpBal = CURVE_LP.balanceOf(address(this));
        if (lpBal > 0) {
            require(BOOSTER.deposit(PID, lpBal, true), "deposit failed");
        }
    }

    function _calcSharesToWithdraw(
        uint _amount,
        uint _total,
        uint _totalShares
    ) private pure returns (uint) {
        /*
        calculate shares to withdraw

        a = amount of ETH to withdraw
        T = total amount of ETH locked in external liquidity pool
        s = shares to withdraw
        P = total shares deposited into external liquidity pool

        a / T = s / P
        s = a / T * P
        */
        if (_total > 0) {
            // avoid rounding errors and cap shares to be <= total shares
            if (_amount >= _total) {
                return _totalShares;
            }
            return _amount.mul(_totalShares) / _total;
        }
        return 0;
    }

    function _removeLiquidity(uint _shares, uint _min) internal virtual;

    function _withdraw(uint _amount) internal override {
        uint bal = address(this).balance;
        if (_amount <= bal) {
            return;
        }

        uint total = _totalAssets();

        if (_amount >= total) {
            _amount = total;
        }

        uint need = _amount - bal;
        uint totalShares = BASE_REWARD_POOL.balanceOf(address(this));
        // total assets is always >= bal
        uint shares = _calcSharesToWithdraw(need, total - bal, totalShares);

        // withdraw from Convex
        if (shares > 0) {
            // true = claim CRV
            require(
                BASE_REWARD_POOL.withdrawAndUnwrap(shares, false),
                "base reward pool withdraw failed"
            );
        }

        // withdraw from Curve
        uint lpBal = CURVE_LP.balanceOf(address(this));
        if (shares > lpBal) {
            shares = lpBal;
        }

        if (shares > 0) {
            uint min = need.mul(SLIP_MAX - slip) / SLIP_MAX;
            _removeLiquidity(shares, min);
        }
    }

    function _harvest() internal override {
        require(
            BASE_REWARD_POOL.getReward(address(this), shouldClaimExtras),
            "get reward failed"
        );

        for (uint i = 0; i < rewards.length; i++) {
            Reward storage reward = rewards[i];
            if (reward.disabled) {
                continue;
            }

            uint bal = IERC20(reward.addr).balanceOf(address(this));
            if (bal > 0) {
                _swapToEth(reward.dex, reward.addr, bal);
            }
        }
    }

    function sweep(address _token) external override onlyAuthorized {
        for (uint i = 0; i < rewards.length; i++) {
            require(_token != rewards[i].addr, "protected token");
        }
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
