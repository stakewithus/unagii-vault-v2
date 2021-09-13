// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../interfaces/convex/BaseRewardPool.sol";
import "../interfaces/convex/Booster.sol";
import "../interfaces/curve/DepositObtc.sol";
import "../interfaces/curve/StableSwapObtc.sol";
import "../base/Strategy.sol";

contract StrategyConvexObtc is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    // Uniswap and Sushiswap //
    // UNISWAP = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    // SUSHISWAP = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    // address of DEX (uniswap or sushiswap) to use for selling reward tokens
    // CRV, CVX, BOR
    address[3] public dex;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;
    address private constant BOR = 0x3c9d6c1C73b31c837832c72E04D3152f051fc1A9;

    // Solc 0.7 cannot create constant arrays
    address[3] private REWARDS = [CRV, CVX, BOR];

    // Convex //
    Booster private constant BOOSTER =
        Booster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    // pool id
    uint private constant PID = 20;
    BaseRewardPool private constant REWARD =
        BaseRewardPool(0xeeeCE77e0bc5e59c77fc408789A9A172A504bD2f);
    bool public shouldClaimExtras = true;

    // Curve //
    // Deposit
    DepositObtc private constant ZAP =
        DepositObtc(0xd5BCf53e2C81e1991570f33Fa881c49EEa570C8D);
    // StableSwap
    StableSwapObtc private constant CURVE_POOL =
        StableSwapObtc(0xd81dA8D904b52208541Bade1bD6595D8a251F8dd);
    // LP token for curve pool bBTC/sbtcCRV
    IERC20 private constant CURVE_LP =
        IERC20(0x2fE94ea3d5d4a175184081439753DE15AeF9d614);

    // prevent slippage from deposit / withdraw
    uint public slip = 100;
    uint private constant SLIP_MAX = 10000;

    /*
    0 - oBTC
    1 - renBTC
    2 - WBTC
    3 - SBTC
    */
    // multipliers to normalize token decimals to 1e18
    uint[4] private MULS = [1, 1e10, 1e10, 1];
    uint private immutable MUL; // multiplier of token
    uint private immutable INDEX; // index of token

    // WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit,
        uint _index
    ) Strategy(_token, _vault, _treasury, _minProfit, _maxProfit) {
        // only WBTC
        require(_index == 2, "index != 2");
        INDEX = _index;
        MUL = MULS[_index];

        (address lptoken, , , address crvRewards, , ) = BOOSTER.poolInfo(PID);
        require(address(CURVE_LP) == lptoken, "curve pool lp != pool info lp");
        require(address(REWARD) == crvRewards, "reward != pool info reward");

        // deposit token into ZAP
        IERC20(_token).safeApprove(address(ZAP), type(uint).max);
        // deposit into BOOSTER
        CURVE_LP.safeApprove(address(BOOSTER), type(uint).max);
        // withdraw from ZAP
        CURVE_LP.safeApprove(address(ZAP), type(uint).max);

        _setDex(0, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CRV - sushiswap
        _setDex(1, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CVX - sushiswap
        _setDex(2, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // BOR - sushiswap
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

    function setDex(uint _i, address _dex) external onlyTimeLockOrAdmin {
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

    function _totalAssets() internal view override returns (uint) {
        /*
        s0 = shares in curve pool
        p0 = price per share of curve pool
        a = amount of tokens

        a = s0 * p0
        */
        // amount of Curve LP tokens in Convex
        uint lpBal = REWARD.balanceOf(address(this));
        uint bal = lpBal.mul(CURVE_POOL.get_virtual_price()) / (MUL * 1e18);

        bal = bal.add(token.balanceOf(address(this)));

        return bal;
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

            ZAP.add_liquidity(amounts, min);
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
            ZAP.remove_liquidity_one_coin(shares, int128(INDEX), min);
        }
    }

    function _harvest() internal override {
        require(
            REWARD.getReward(address(this), shouldClaimExtras),
            "get reward failed"
        );

        for (uint i = 0; i < REWARDS.length; i++) {
            uint rewardBal = IERC20(REWARDS[i]).balanceOf(address(this));
            if (rewardBal > 0) {
                // swap may fail if rewards are too small
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
        for (uint i = 0; i < REWARDS.length; i++) {
            require(_token != REWARDS[i], "protected token");
        }
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
