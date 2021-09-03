// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// version 1.0.0

import "../interfaces/convex/BaseRewardPool.sol";
import "../interfaces/convex/Booster.sol";
import "../interfaces/curve/StableSwapStEth.sol";
import "../base/StrategyEth.sol";

contract StrategyConvexStEth is StrategyEth {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    // Uniswap and Sushiswap //
    // UNISWAP = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    // SUSHISWAP = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    uint private constant NUM_REWARDS = 3;
    // address of DEX (uniswap or sushiswap) to use for selling reward tokens
    // CRV, CVX, LDO
    address[NUM_REWARDS] public dex;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant LDO = 0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32;

    // Solc 0.7 cannot create constant arrays
    address[NUM_REWARDS] private REWARDS = [CRV, CVX, LDO];

    // Convex //
    Booster private constant BOOSTER =
        Booster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    // pool id
    uint private constant PID = 25;
    BaseRewardPool private constant REWARD =
        BaseRewardPool(0x0A760466E1B4621579a82a39CB56Dda2F4E70f03);
    bool public shouldClaimExtras = true;

    // Curve //
    // StableSwap StETH
    StableSwapStEth private constant CURVE_POOL =
        StableSwapStEth(0xDC24316b9AE028F1497c275EB9192a3Ea0f67022);
    // LP token for curve pool (ETH / stETH)
    IERC20 private constant CURVE_LP =
        IERC20(0x06325440D014e39736583c165C2963BA99fAf14E);

    // prevent slippage from deposit / withdraw
    uint public slip = 100;
    uint private constant SLIP_MAX = 10000;

    /*
    0 - ETH
    1 - stETH
    */
    uint private constant INDEX = 0; // index of token

    constructor(
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    ) StrategyEth(_vault, _treasury, _minProfit, _maxProfit) {
        (address lptoken, , , address crvRewards, , ) = BOOSTER.poolInfo(PID);
        require(address(CURVE_LP) == lptoken, "curve pool lp != pool info lp");
        require(address(REWARD) == crvRewards, "reward != pool info reward");

        // deposit into BOOSTER
        CURVE_LP.safeApprove(address(BOOSTER), type(uint).max);

        _setDex(0, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CRV - sushiswap
        _setDex(1, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CVX - sushiswap
        _setDex(2, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // LDO - sushiswap
    }

    function _setDex(uint _i, address _dex) private {
        IERC20 reward = IERC20(REWARDS[_i]);

        // disallow previous dex
        if (dex[_i] != address(0)) {
            reward.safeApprove(dex[_i], 0);
        }

        dex[_i] = _dex;

        // approve new dex
        reward.safeApprove(_dex, type(uint).max);
    }

    function setDex(uint _i, address _dex) external onlyTimeLock {
        require(_dex != address(0), "dex = 0 address");
        _setDex(_i, _dex);
    }

    /*
    @notice Set max slippage for deposit and withdraw from Curve pool
    @param _slip Max amount of slippage allowed
    */
    function setSlip(uint _slip) external onlyAuthorized {
        require(_slip <= SLIP_MAX, "slip > max");
        slip = _slip;
    }

    // @dev Claim extra rewards from Convex
    function setShouldClaimExtras(bool _shouldClaimExtras) external onlyAuthorized {
        shouldClaimExtras = _shouldClaimExtras;
    }

    function _totalAssets() internal view override returns (uint total) {
        /*
        s0 = shares in curve pool
        p0 = price per share of curve pool
        a = amount of ETH

        a = s0 * p0
        */
        // amount of Curve LP tokens in Convex
        uint lpBal = REWARD.balanceOf(address(this));
        // amount of ETH converted from Curve LP
        total = lpBal.mul(CURVE_POOL.get_virtual_price()) / 1e18;

        total = total.add(address(this).balance);
    }

    function _deposit() internal override {
        uint bal = address(this).balance;
        if (bal > 0) {
            uint[2] memory amounts;
            amounts[INDEX] = bal;
            /*
            shares = ETH amount * 1e18 / price per share
            */
            uint pricePerShare = CURVE_POOL.get_virtual_price();
            uint shares = bal.mul(1e18).div(pricePerShare);
            uint min = shares.mul(SLIP_MAX - slip) / SLIP_MAX;

            CURVE_POOL.add_liquidity{value: bal}(amounts, min);
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
        uint totalShares = REWARD.balanceOf(address(this));
        // total assets is always >= bal
        uint shares = _calcSharesToWithdraw(need, total - bal, totalShares);

        // withdraw from Convex
        if (shares > 0) {
            // true = claim CRV
            require(REWARD.withdrawAndUnwrap(shares, false), "reward withdraw failed");
        }

        // withdraw from Curve
        uint lpBal = CURVE_LP.balanceOf(address(this));
        if (shares > lpBal) {
            shares = lpBal;
        }

        if (shares > 0) {
            uint min = need.mul(SLIP_MAX - slip) / SLIP_MAX;
            CURVE_POOL.remove_liquidity_one_coin(shares, int128(INDEX), min);
        }
    }

    function harvest(uint _minProfit) external override onlyAuthorized {
        // calculate profit = balance of ETH after - balance of ETH before
        uint diff = address(this).balance;

        require(
            REWARD.getReward(address(this), shouldClaimExtras),
            "get reward failed"
        );

        for (uint i = 0; i < NUM_REWARDS; i++) {
            uint rewardBal = IERC20(REWARDS[i]).balanceOf(address(this));
            if (rewardBal > 0) {
                _swapToEth(dex[i], REWARDS[i], rewardBal);
            }
        }

        diff = address(this).balance - diff;
        require(diff >= _minProfit, "profit < min");

        // transfer performance fee to treasury
        if (diff > 0) {
            uint fee = _calcFee(diff);
            if (fee > 0) {
                _sendEth(treasury, fee);
            }
        }
    }

    /*
    @notice Transfer token accidentally sent here to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external override onlyAuthorized {
        for (uint i = 0; i < NUM_REWARDS; i++) {
            require(_token != REWARDS[i], "protected token");
        }
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
