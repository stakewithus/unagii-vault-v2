// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// TODO: uniswap v3?
import "../interfaces/uniswap/UniswapV2Router.sol";
import "../interfaces/convex/BaseRewardPool.sol";
import "../interfaces/convex/Booster.sol";
import "../interfaces/curve/CurveAlUsd3Pool.sol";
import "../Strategy.sol";

contract StrategyConvexAlUsd is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    // Uniswap //
    // TODO: check contract addresses still active
    UniswapV2Router public uniswap =
        UniswapV2Router(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    // min profit harvest should make
    uint public minProfit;

    // Convex //
    Booster private constant booster =
        Booster(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    IERC20 private constant cvx = IERC20(0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B);
    // pool id
    uint private constant PID = 36;
    BaseRewardPool private constant reward =
        BaseRewardPool(0x02E2151D4F351881017ABdF2DD2b51150841d5B3);

    // Alchemist //
    IERC20 private constant alcx = IERC20(0xdBdb4d16EdA451D0503b854CF79D55697F90c8DF);

    // Curve //
    // 3Pool
    CurveAlUsd3Pool private constant curve =
        CurveAlUsd3Pool(0xA79828DF1850E8a3A3064576f380D90aECDD3359);
    // Metapool AlUsd 3CRV
    address private constant POOL = 0x43b4FdFD4Ff969587185cDB6f0BD875c5Fc83f8c;
    IER20 private constant crv = IERC20(0xD533a949740bb3306d119CC777fa900bA034cd52);

    IERC20 private constant dai = IERC20(0x6B175474E89094C44Da98b954EedeAC495271d0F);
    IERC20 private constant usdc = IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    IERC20 private constant usdt = IERC20(0xdAC17F958D2ee523a2206206994597C13D831ec7);

    constructor(
        address _token,
        address _fundManager,
        address _treasury
    ) Strategy(_token, _fundManager, _treasury) {}

    function _totalAssets() private view returns (uint) {
        // return Rewards(rewardContract).balanceOf(address(this)) x virtual price;
        return 0;
    }

    function totalAssets() external view override returns (uint) {
        return _totalAssets();
    }

    function _deposit() private {
        require(booster.deposit(ID, CURVE_LP, true), "deposit failed");
    }

    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        require(_amount > 0, "deposit = 0");

        uint borrowed = fundManager.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");

        _deposit();
        emit Deposit(_amount, borrowed);
    }

    function _withdraw(uint _amount) private returns (uint) {
        // Rewards(rewardContract).withdrawAndUnwrap(_amount, false);
        return 0;
    }

    function withdraw(uint _amount) external override onlyFundManager returns (uint) {
        require(_amount > 0, "withdraw = 0");

        // availabe <= _amount
        uint available = _withdraw(_amount);

        uint loss = 0;
        uint debt = fundManager.getDebt(address(this));
        uint total = _totalAssets();
        if (debt > total) {
            loss = debt - total;
        }

        if (available > 0) {
            token.safeTransfer(msg.sender, available);
        }

        emit Withdraw(_amount, available);

        return loss;
    }

    function repay(uint _amount, uint _min) external override {
        require(_amount > 0, "repay = 0");
        // availabe <= _amount
        uint available = _withdraw(_amount);
        uint repaid = fundManager.repay(available);
        require(repaid >= _min, "repaid < min");

        emit Repay(_amount, repaid);
    }

    function setUniswap(address _uni) external onlyTimeLock {
        if (address(uniswap) != address(0)) {
            // comp.safeApprove(address(uniswap), 0);
        }

        uniswap = UniswapV2Router(_uni);
        // comp.safeApprove(address(uniswap), type(uint).max);
    }

    function setMinProfit(uint _minProfit) external onlyAuthorized {
        minProfit = _minProfit;
    }

    /*
    @dev Uniswap fails with zero address so no check is necessary here
    */
    function _swap(
        address _tokenIn,
        address _toKenOut,
        uint _amount
    ) private {
        // create dynamic array with 3 elements
        address[] memory path = new address[](3);
        path[0] = _tokenIn;
        path[1] = WETH;
        path[2] = _tokenOut;

        uniswap.swapExactTokensForTokens(
            _amount,
            1,
            path,
            address(this),
            block.timestamp
        );
    }

    function _claimRewards() private {
        // TODO: isClaimExtras
        bool isClaimExtras = true;
        require(reward.getReward(address(this), isClaimExtras), "get reward failed");

        uint crvBal = crv.balanceOf(address(this));
        if (crvBal > 0) {
            // TODO: liquidity
            _swap(address(crv), address(token), crvBal);
        }

        uint cvxBal = cvx.balanceOf(address(this));
        if (cvxBal > 0) {
            // TODO: liquidity
            _swap(address(cvx), address(token), cvxBal);
        }

        uint alcxBal = alcx.balanceOf(address(this));
        if (alcxBal > 0) {
            // TODO: liquidity
            _swap(address(alcx), address(token), alcxBal);
        }

        uint daiBal = dai.balanceOf(address(this));
        uint usdcBal = usdc.balanceOf(address(this));
        uint usdtBal = usdt.balanceOf(address(this));
        if (daiBal > 0 || usdcBal > 0 || usdtBal > 0) {
            curve.add_liquidity(POOL, [0, daiBal, usdcBal, usdtBal], 0);
        }
    }

    /*
    @notice Claim and sell any rewards
    */
    function harvest() external override onlyAuthorized {
        uint balBefore = token.balanceOf(address(this));
        _claimRewards();
        uint balAfter = token.balanceOf(address(this)) - balBefore;
        uint diff = balAfter - balBefore;

        require(diff >= minProfit, "profit < min");

        uint profit = 0;
        if (balAfter > 0) {
            // transfer fee to treasury
            uint fee = balAfter.mul(perfFee) / PERF_FEE_MAX;
            if (fee > 0) {
                token.safeTransfer(treasury, fee);
            }
            profit = balAfter.sub(fee);
            // _supply() to decrease collateral ratio and earn interest
            // use _supply() instead of _deposit() to save gas
            // TODO: supply?
            // _supply(profit);
        }

        emit Harvest(profit);
    }

    function skim() external override onlyAuthorized {
        uint total = _totalAssets();
        uint debt = fundManager.getDebt(address(this));
        require(total > debt, "total <= debt");

        uint profit = total - debt;
        // reassign to actual amount withdrawn
        profit = _withdraw(profit);

        emit Skim(profit);
    }

    function report(uint _min, uint _max) external override onlyAuthorized {
        uint total = _totalAssets();
        require(total >= _min, "total < min");
        require(total <= _max, "total > max");

        // TODO:
        // _harvest();
        // _skim();

        uint gain = 0;
        uint loss = 0;
        uint debt = fundManager.getDebt(address(this));

        if (total > debt) {
            gain = total - debt;

            uint bal = token.balanceOf(address(this));
            if (gain > bal) {
                gain = bal;
            }
        } else {
            loss = debt - total;
        }

        if (gain > 0 || loss > 0) {
            fundManager.report(gain, loss);
        }

        /// TODO: borrow more or repay

        emit Report(gain, loss);
    }

    function migrate(address _strategy) external override onlyFundManager {
        Strategy strat = Strategy(_strategy);
        // TODO: is this checking interface type or address?
        require(strat.token() == token, "strategy token != token");
        require(
            strat.fundManager() == fundManager,
            "strategy fund manager != fund manager"
        );

        // TODO: _harvest();
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
        require(_token != CRV, "protected token");
        require(_token != CVX, "protected token");
        require(_token != ALCX, "protected token");
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
