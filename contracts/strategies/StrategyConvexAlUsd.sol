// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// version 1.0.0

import "../interfaces/convex/BaseRewardPool.sol";
import "../interfaces/convex/Booster.sol";
import "../interfaces/curve/DepositZapAlUsd3Crv.sol";
import "../interfaces/curve/StableSwapAlUsd3Crv.sol";
import "../base/Strategy.sol";

contract StrategyConvexAlUsd is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    uint private constant NUM_REWARDS = 3;
    // address of DEX (uniswap or sushiswap) to use for selling reward tokens
    // CRV, CVX, ALCX
    address[NUM_REWARDS] public dex;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant ALCX = 0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF;

    // Solc 0.7 cannot create constant arrays
    address[NUM_REWARDS] private REWARDS = [CRV, CVX, ALCX];

    // Convex //
    Booster private constant BOOSTER =
        Booster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    // pool id
    uint private constant PID = 36;
    BaseRewardPool private constant REWARD =
        BaseRewardPool(0x02E2151D4F351881017ABdF2DD2b51150841d5B3);
    bool public shouldClaimExtras = true;

    // Curve //
    // DepositZap alUSD + 3CRV
    DepositZapAlUsd3Crv private constant ZAP =
        DepositZapAlUsd3Crv(0xA79828DF1850E8a3A3064576f380D90aECDD3359);
    // StableSwap alUSD + 3CRV (meta pool)
    StableSwapAlUsd3Crv private constant CURVE_POOL =
        StableSwapAlUsd3Crv(0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c);
    // LP token for curve pool (same contract as CURVE_POOL)
    IERC20 private constant CURVE_LP =
        IERC20(0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c);

    // prevent slippage from deposit / withdraw
    uint public slip = 100;
    uint private constant SLIP_MAX = 10000;

    /*
    0 - alUSD
    1 - DAI
    2 - USDC
    3 - USDT
    */
    // multipliers to normalize token decimals to 1e18
    uint[4] private MULS = [1, 1, 1e12, 1e12];
    uint private immutable MUL; // multiplier of token
    uint private immutable INDEX; // index of token

    // DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F
    // USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
    // USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit,
        uint _index
    ) Strategy(_token, _vault, _treasury, _minProfit, _maxProfit) {
        // disable alUSD
        require(_index > 0, "index = 0");
        INDEX = _index;
        MUL = MULS[_index];

        (address lptoken, , , address crvRewards, , ) = BOOSTER.poolInfo(PID);
        require(address(CURVE_LP) == lptoken, "curve pool lp != pool info lp");
        require(address(REWARD) == crvRewards, "reward != pool info reward");

        IERC20(_token).safeApprove(address(ZAP), type(uint).max);
        // deposit into BOOSTER
        CURVE_LP.safeApprove(address(BOOSTER), type(uint).max);
        // withdraw from ZAP
        CURVE_LP.safeApprove(address(ZAP), type(uint).max);

        _setDex(0, SUSHISWAP); // CRV
        _setDex(1, SUSHISWAP); // CVX
        _setDex(2, SUSHISWAP); // ALCX
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

    // @dev Claim extra rewards (ALCX) from Convex
    function setShouldClaimExtras(bool _shouldClaimExtras) external onlyAuthorized {
        shouldClaimExtras = _shouldClaimExtras;
    }

    function _totalAssets() internal view override returns (uint total) {
        /*
        s0 = shares in meta pool
        p0 = price per share of meta pool
        s1 = shares in base pool
        p1 = price per share of base pool
        a = amount of tokens (DAI, USDC, USDT)

        s1 = s0 * p0
        a = s1 * p1

        a = s0 * p0 * p1
        */
        // amount of Curve LP tokens in Convex
        uint lpBal = REWARD.balanceOf(address(this));
        // amount of alUSD or DAI, USDC, USDT converted from Curve LP
        // BASE_POOL.get_virtual_price is included in CURVE_POOL.get_virtual_price
        // so CURVE_POOL.get_virtual_price = p0 * p1
        total = lpBal.mul(CURVE_POOL.get_virtual_price()) / (MUL * 1e18);
        total = total.add(token.balanceOf(address(this)));
    }

    function _deposit() internal override {
        uint bal = token.balanceOf(address(this));
        if (bal > 0) {
            uint[4] memory amounts;
            amounts[INDEX] = bal;
            /*
            shares = token amount * multiplier * 1e18 / price per share
            */
            uint pricePerShare = CURVE_POOL.get_virtual_price();
            uint shares = bal.mul(MUL).mul(1e18).div(pricePerShare);
            uint min = shares.mul(SLIP_MAX - slip) / SLIP_MAX;

            ZAP.add_liquidity(address(CURVE_POOL), amounts, min);
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

        a = amount of token to withdraw
        T = total amount of token locked in external liquidity pool
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
        uint bal = token.balanceOf(address(this));
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
            // true = claim CRV and ALCX
            require(REWARD.withdrawAndUnwrap(shares, false), "reward withdraw failed");
        }

        // withdraw from Curve
        uint lpBal = CURVE_LP.balanceOf(address(this));
        if (shares > lpBal) {
            shares = lpBal;
        }

        if (shares > 0) {
            uint min = need.mul(SLIP_MAX - slip) / SLIP_MAX;
            ZAP.remove_liquidity_one_coin(
                address(CURVE_POOL),
                shares,
                int128(INDEX),
                min
            );
        }
    }

    function _harvest() internal override {
        require(
            REWARD.getReward(address(this), shouldClaimExtras),
            "get reward failed"
        );

        for (uint i = 0; i < NUM_REWARDS; i++) {
            uint rewardBal = IERC20(REWARDS[i]).balanceOf(address(this));
            if (rewardBal > 0) {
                _swap(dex[i], REWARDS[i], address(token), rewardBal);
            }
        }
    }

    /*
    @notice Transfer token accidentally sent here to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(token), "protected token");
        for (uint i = 0; i < NUM_REWARDS; i++) {
            require(_token != REWARDS[i], "protected token");
        }
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
