// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// version 0.1.1

import "../interfaces/uniswap/UniswapV2Router.sol";
import "../interfaces/convex/BaseRewardPool.sol";
import "../interfaces/convex/Booster.sol";
import "../interfaces/curve/DepositBbtc.sol";
import "../interfaces/curve/StableSwapBbtc.sol";
import "../base/Strategy.sol";

contract StrategyConvexBbtc is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    // Uniswap and Sushiswap //
    // UNISWAP = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    // SUSHISWAP = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    uint private constant NUM_REWARDS = 2;
    // address of DEX (uniswap or sushiswap) to use for selling reward tokens
    // CRV, CVX
    address[NUM_REWARDS] public dex;

    address private constant CRV = 0xD533a949740bb3306d119CC777fa900bA034cd52;
    address private constant CVX = 0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B;

    // Solc 0.7 cannot create constant arrays
    address[NUM_REWARDS] private REWARDS = [CRV, CVX];

    // Convex //
    Booster private constant BOOSTER =
        Booster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    // pool id
    uint private constant PID = 19;
    BaseRewardPool private constant REWARD =
        BaseRewardPool(0x61D741045cCAA5a215cF4E5e55f20E1199B4B843);
    bool public shouldClaimExtras = true;

    // Curve //
    // Deposit
    DepositBbtc private constant ZAP =
        DepositBbtc(0xC45b2EEe6e09cA176Ca3bB5f7eEe7C47bF93c756);
    // StableSwap
    StableSwapBbtc private constant CURVE_POOL =
        StableSwapBbtc(0x42d7025938bEc20B69cBae5A77421082407f053A);
    // LP token for curve pool bBTC/sbtcCRV
    IERC20 private constant CURVE_LP =
        IERC20(0x410e3E86ef427e30B9235497143881f717d93c2A);

    // prevent slippage from deposit / withdraw
    uint public slip = 100;
    uint private constant SLIP_MAX = 10000;

    /*
    0 - BBTC
    1 - renBTC
    2 - WBTC
    3 - SBTC
    */
    // multipliers to normalize token decimals to 10 ** 18
    uint[4] private MULS = [1e10, 1e10, 1e10, 1];
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

        IERC20(_token).safeApprove(address(ZAP), type(uint).max);
        // deposit into BOOSTER
        CURVE_LP.safeApprove(address(BOOSTER), type(uint).max);
        // withdraw from ZAP
        CURVE_LP.safeApprove(address(ZAP), type(uint).max);

        _setDex(0, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CRV - sushiswap
        _setDex(1, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // CVX - sushiswap
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

    function _totalAssets() private view returns (uint total) {
        /*
        s0 = shares in curve pool
        p0 = price per share of curve pool
        a = amount of tokens

        a = s0 * p0
        */
        // amount of Curve LP tokens in Convex
        uint lpBal = REWARD.balanceOf(address(this));
        total = lpBal.mul(CURVE_POOL.get_virtual_price()) / (MUL * 1e18);
        total = total.add(token.balanceOf(address(this)));
    }

    function totalAssets() external view override returns (uint) {
        return _totalAssets();
    }

    function _deposit() private {
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

    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        // TODO: deposit with borrow = 0
        require(_amount > 0, "deposit = 0");

        uint borrowed = vault.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");

        _deposit();
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

    function _withdraw(uint _amount) private returns (uint) {
        uint bal = token.balanceOf(address(this));
        if (_amount <= bal) {
            return _amount;
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

        uint balAfter = token.balanceOf(address(this));
        if (balAfter < _amount) {
            return balAfter;
        }
        // balAfter >= _amount >= total
        // requested to withdraw all so return balAfter
        if (_amount >= total) {
            return balAfter;
        }
        // requested withdraw < all
        return _amount;
    }

    function withdraw(uint _amount) external override onlyVault {
        require(_amount > 0, "withdraw = 0");

        // availabe <= _amount
        uint available = _withdraw(_amount);

        if (available > 0) {
            token.safeTransfer(msg.sender, available);
        }
    }

    function repay(uint _amount, uint _min) external override onlyAuthorized {
        require(_amount > 0, "repay = 0");
        // availabe <= _amount
        uint available = _withdraw(_amount);
        uint repaid = vault.repay(available);
        require(repaid >= _min, "repaid < min");
    }

    /*
    @dev Uniswap fails with zero address so no check is necessary here
    */
    function _swap(
        address _dex,
        address _tokenIn,
        address _tokenOut,
        uint _amount
    ) private {
        // create dynamic array with 3 elements
        address[] memory path = new address[](3);
        path[0] = _tokenIn;
        path[1] = WETH;
        path[2] = _tokenOut;

        UniswapV2Router(_dex).swapExactTokensForTokens(
            _amount,
            1,
            path,
            address(this),
            block.timestamp
        );
    }

    function _harvest(uint _minProfit) private {
        // calculate profit = balance of token after - balance of token before
        uint diff = token.balanceOf(address(this));

        require(
            REWARD.getReward(address(this), shouldClaimExtras),
            "get reward failed"
        );

        for (uint i = 0; i < NUM_REWARDS; i++) {
            uint rewardBal = IERC20(REWARDS[i]).balanceOf(address(this));
            if (rewardBal > 0) {
                // swap may fail if rewards are too small
                _swap(dex[i], REWARDS[i], address(token), rewardBal);
            }
        }

        diff = token.balanceOf(address(this)) - diff;
        require(diff >= _minProfit, "profit < min");

        // transfer performance fee to treasury
        if (diff > 0) {
            uint fee = _calcFee(diff);
            if (fee > 0) {
                token.safeTransfer(treasury, fee);
            }
        }
    }

    function harvest(uint _minProfit) external override onlyAuthorized {
        _harvest(_minProfit);
    }

    function migrate(address _strategy) external override onlyVault {
        Strategy strat = Strategy(_strategy);
        require(address(strat.token()) == address(token), "strategy token != token");
        require(address(strat.vault()) == address(vault), "strategy vault != vault");

        if (!skipHarvest) {
            _harvest(1);
        }

        uint bal = _withdraw(type(uint).max);
        token.safeApprove(_strategy, bal);
        strat.pull(address(this), bal);
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
