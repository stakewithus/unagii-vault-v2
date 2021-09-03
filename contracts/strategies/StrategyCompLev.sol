// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// version 0.1.1

import "../interfaces/uniswap/UniswapV2Router.sol";
import "../interfaces/compound/CErc20.sol";
import "../interfaces/compound/Comptroller.sol";
import "../base/Strategy.sol";

/*
APY estimate
c = collateral ratio
i_s = supply interest rate (APY)
i_b = borrow interest rate (APY)
c_s = supply COMP reward (APY)
c_b = borrow COMP reward (APY)
leverage APY = 1 / (1 - c) * (i_s + c_s - c * (i_b - c_b))
plugging some numbers
31.08 = 4 * (7.01 + 4 - 0.75 * (9.08 - 4.76))
*/

/*
State transitions and valid transactions
### State ###
buff = buffer
s = supplied
b = borrowed
### Transactions ###
dl = deleverage
l = leverage
w = withdraw
d = deposit
s(x) = set butter to x
### State Transitions ###
                             s(max)
(buf = max, s > 0, b > 0) <--------- (buf = min, s > 0, b > 0)
          |                               |        ^
          | dl, w                         | dl, w  | l, d
          |                               |        |
          V                               V        | 
(buf = max, s > 0, b = 0) ---------> (buf = min, s > 0, b = 0)
                             s(min)
*/

contract StrategyCompLev is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    // Uniswap and Sushiswap //
    // UNISWAP = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    // SUSHISWAP = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public dex;

    // Compound //
    Comptroller private constant comptroller =
        Comptroller(0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B);
    IERC20 private constant comp = IERC20(0xc00e94Cb662C3520282E6f5717214004A7f26888);
    CErc20 private immutable cToken;
    uint public buffer = 0.04 * 1e18;

    constructor(
        address _token,
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit,
        address _cToken
    ) Strategy(_token, _vault, _treasury, _minProfit, _maxProfit) {
        require(_cToken != address(0), "cToken = zero address");
        cToken = CErc20(_cToken);
        IERC20(_token).safeApprove(_cToken, type(uint).max);
        // TODO: use uniswap 3?
        _setDex(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // Sushiswap
    }

    function _setDex(address _dex) private {
        if (dex != address(0)) {
            comp.safeApprove(dex, 0);
        }

        dex = _dex;
        comp.safeApprove(_dex, type(uint).max);
    }

    function setDex(address _dex) external onlyTimeLock {
        require(_dex != address(0), "dex = 0 address");
        _setDex(_dex);
    }

    function _totalAssets() private view returns (uint total) {
        // WARNING: This returns balance last time someone transacted with cToken
        (uint err, uint cTokenBal, uint borrowed, uint exchangeRate) = cToken
        .getAccountSnapshot(address(this));

        if (err > 0) {
            // something is wrong, return 0
            return 0;
        }
        uint supplied = cTokenBal.mul(exchangeRate) / 1e18;
        if (supplied < borrowed) {
            // something is wrong, return 0
            return 0;
        }
        total = token.balanceOf(address(this)).add(supplied - borrowed);
    }

    /*
    @notice Returns amount of tokens locked in this contract
    */
    function totalAssets() external view override returns (uint) {
        return _totalAssets();
    }

    /*
    @dev buffer = 0 means safe collateral ratio = market collateral ratio
         buffer = 1e18 means safe collateral ratio = 0
    */
    function setBuffer(uint _buffer) external onlyAuthorized {
        require(_buffer > 0 && _buffer <= 1e18, "buffer");
        buffer = _buffer;
    }

    function _getMarketCollateralRatio() private view returns (uint) {
        /*
        This can be changed by Compound Governance, with a minimum waiting
        period of five days
        */
        (, uint col, ) = comptroller.markets(address(cToken));
        return col;
    }

    function _getSafeCollateralRatio(uint _marketCol) private view returns (uint) {
        if (_marketCol > buffer) {
            return _marketCol - buffer;
        }
        return 0;
    }

    // Not view function
    function _getSupplied() private returns (uint) {
        return cToken.balanceOfUnderlying(address(this));
    }

    // Not view function
    function _getBorrowed() private returns (uint) {
        return cToken.borrowBalanceCurrent(address(this));
    }

    // Not view function. Call using static call from web3
    function getLivePosition()
        external
        returns (
            uint supplied,
            uint borrowed,
            uint marketCol,
            uint safeCol
        )
    {
        supplied = _getSupplied();
        borrowed = _getBorrowed();
        marketCol = _getMarketCollateralRatio();
        safeCol = _getSafeCollateralRatio(marketCol);
    }

    // @dev This returns balance last time someone transacted with cToken
    function getCachedPosition()
        external
        view
        returns (
            uint supplied,
            uint borrowed,
            uint marketCol,
            uint safeCol
        )
    {
        // ignore first output, which is error code
        (, uint cTokenBal, uint _borrowed, uint exchangeRate) = cToken
        .getAccountSnapshot(address(this));
        supplied = cTokenBal.mul(exchangeRate) / 1e18;
        borrowed = _borrowed;
        marketCol = _getMarketCollateralRatio();
        safeCol = _getSafeCollateralRatio(marketCol);
    }

    // @dev This modifier checks collateral ratio after leverage or deleverage
    modifier checkCollateralRatio() {
        _;
        uint supplied = _getSupplied();
        uint borrowed = _getBorrowed();
        uint marketCol = _getMarketCollateralRatio();
        uint safeCol = _getSafeCollateralRatio(marketCol);
        // borrowed / supplied <= safe col
        // supplied can = 0 so we check borrowed <= supplied * safe col
        // max borrow
        uint max = supplied.mul(safeCol) / 1e18;
        require(borrowed <= max, "borrowed > max");
    }

    // @dev In case infinite approval is reduced so that strategy cannot function
    function approve(uint _amount) external onlyAuthorized {
        token.safeApprove(address(cToken), _amount);
    }

    function _supply(uint _amount) private {
        require(cToken.mint(_amount) == 0, "mint");
    }

    // @dev Execute manual recovery by admin
    // @dev `_amount` must be >= balance of token
    function supplyManual(uint _amount) external onlyAuthorized {
        _supply(_amount);
    }

    function _borrow(uint _amount) private {
        require(cToken.borrow(_amount) == 0, "borrow");
    }

    // @dev Execute manual recovery by admin
    function borrowManual(uint _amount) external onlyAuthorized {
        _borrow(_amount);
    }

    function _repay(uint _amount) private {
        require(cToken.repayBorrow(_amount) == 0, "repay");
    }

    // @dev Execute manual recovery by admin
    // @dev `_amount` must be >= balance of token
    function repayManual(uint _amount) external onlyAuthorized {
        _repay(_amount);
    }

    function _redeem(uint _amount) private {
        require(cToken.redeemUnderlying(_amount) == 0, "redeem");
    }

    // @dev Execute manual recovery by admin
    function redeemManual(uint _amount) external onlyAuthorized {
        _redeem(_amount);
    }

    function _getMaxLeverageRatio(uint _col) private pure returns (uint) {
        /*
        c = collateral ratio
        geometric series converges to
            1 / (1 - c)
        */
        // multiplied by 1e18
        return uint(1e36).div(uint(1e18).sub(_col));
    }

    function _getBorrowAmount(
        uint _supplied,
        uint _borrowed,
        uint _col
    ) private pure returns (uint) {
        /*
        c = collateral ratio
        s = supplied
        b = borrowed
        x = amount to borrow
        (b + x) / s <= c
        becomes
        x <= sc - b
        */
        // max borrow
        uint max = _supplied.mul(_col) / 1e18;
        if (_borrowed >= max) {
            return 0;
        }
        return max - _borrowed;
    }

    /*
    Find total supply S_n after n iterations starting with
    S_0 supplied and B_0 borrowed
    c = collateral ratio
    S_i = supplied after i iterations
    B_i = borrowed after i iterations
    S_0 = current supplied
    B_0 = current borrowed
    borrowed and supplied after n iterations
        B_n = cS_(n-1)
        S_n = S_(n-1) + (cS_(n-1) - B_(n-1))
    you can prove using algebra and induction that
        B_n / S_n <= c
        S_n - S_(n-1) = c^(n-1) * (cS_0 - B_0)
        S_n = S_0 + sum (c^i * (cS_0 - B_0)), 0 <= i <= n - 1
            = S_0 + (1 - c^n) / (1 - c)
        S_n <= S_0 + (cS_0 - B_0) / (1 - c)
    */
    function _leverage(uint _targetSupply) private checkCollateralRatio {
        // buffer = 1e18 means safe collateral ratio = 0
        if (buffer >= 1e18) {
            return;
        }
        uint supplied = _getSupplied();
        uint borrowed = _getBorrowed();
        uint unleveraged = supplied.sub(borrowed); // supply with 0 leverage
        require(_targetSupply >= supplied, "leverage");
        uint marketCol = _getMarketCollateralRatio();
        uint safeCol = _getSafeCollateralRatio(marketCol);
        uint lev = _getMaxLeverageRatio(safeCol);
        // 99% to be safe, and save gas
        uint max = (unleveraged.mul(lev) / 1e18).mul(9900) / 10000;
        if (_targetSupply >= max) {
            _targetSupply = max;
        }
        uint i;
        while (supplied < _targetSupply) {
            // target is usually reached in 9 iterations
            require(i < 25, "max iteration");
            // use market collateral to calculate borrow amount
            // this is done so that supplied can reach _targetSupply
            // 99.99% is borrowed to be safe
            uint borrowAmount = _getBorrowAmount(supplied, borrowed, marketCol).mul(
                9999
            ) / 10000;
            require(borrowAmount > 0, "borrow = 0");
            if (supplied.add(borrowAmount) > _targetSupply) {
                // borrow > 0 since supplied < _targetSupply
                borrowAmount = _targetSupply.sub(supplied);
            }
            _borrow(borrowAmount);
            // end loop with _supply, this ensures no borrowed amount is unutilized
            _supply(borrowAmount);
            // supplied > _getSupplied(), by about 3 * 1e12 %, but we use local variable to save gas
            supplied = supplied.add(borrowAmount);
            // _getBorrowed == borrowed
            borrowed = borrowed.add(borrowAmount);
            i++;
        }
    }

    function leverage(uint _targetSupply) external onlyAuthorized {
        _leverage(_targetSupply);
    }

    function _deposit() private {
        uint bal = token.balanceOf(address(this));
        if (bal > 0) {
            _supply(bal);
            // leverage to max
            _leverage(type(uint).max);
        }
    }

    /*
    @notice Deposit token into this strategy
    @param _amount Amount of token to deposit
    @param _min Minimum amount to borrow from vault
    */
    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        require(_amount > 0, "deposit = 0");

        uint borrowed = vault.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");

        _deposit();
    }

    function _getRedeemAmount(
        uint _supplied,
        uint _borrowed,
        uint _col
    ) private pure returns (uint) {
        /*
        c = collateral ratio
        s = supplied
        b = borrowed
        r = redeem
        b / (s - r) <= c
        becomes
        r <= s - b / c
        */
        // min supply
        // b / c = min supply needed to borrow b
        uint min = _borrowed.mul(1e18).div(_col);
        if (_supplied <= min) {
            return 0;
        }
        return _supplied - min;
    }

    /*
    Find S_0, amount of supply with 0 leverage, after n iterations starting with
    S_n supplied and B_n borrowed
    c = collateral ratio
    S_n = current supplied
    B_n = current borrowed
    S_(n-i) = supplied after i iterations
    B_(n-i) = borrowed after i iterations
    R_(n-i) = Redeemable after i iterations
        = S_(n-i) - B_(n-i) / c
        where B_(n-i) / c = min supply needed to borrow B_(n-i)
    For 0 <= k <= n - 1
        S_k = S_(k+1) - R_(k+1)
        B_k = B_(k+1) - R_(k+1)
    and
        S_k - B_k = S_(k+1) - B_(k+1)
    so
        S_0 - B_0 = S_1 - S_2 = ... = S_n - B_n
    S_0 has 0 leverage so B_0 = 0 and we get
        S_0 = S_0 - B_0 = S_n - B_n
    ------------------------------------------
    Find S_(n-k), amount of supply, after k iterations starting with
    S_n supplied and B_n borrowed
    with algebra and induction you can derive that
    R_(n-k) = R_n / c^k
    S_(n-k) = S_n - sum R_(n-i), 0 <= i <= k - 1
            = S_n - R_n * ((1 - 1/c^k) / (1 - 1/c))
    Equation above is valid for S_(n - k) k < n
    */
    function _deleverage(uint _targetSupply) private checkCollateralRatio {
        uint supplied = _getSupplied();
        uint borrowed = _getBorrowed();
        uint unleveraged = supplied.sub(borrowed);
        require(_targetSupply <= supplied, "deleverage");
        uint marketCol = _getMarketCollateralRatio();
        // min supply
        if (_targetSupply <= unleveraged) {
            _targetSupply = unleveraged;
        }
        uint i;
        while (supplied > _targetSupply) {
            // target is usually reached in 8 iterations
            require(i < 25, "max iteration");
            // 99.99% to be safe
            uint redeemAmount = (_getRedeemAmount(supplied, borrowed, marketCol)).mul(
                9999
            ) / 10000;
            require(redeemAmount > 0, "redeem = 0");
            if (supplied.sub(redeemAmount) < _targetSupply) {
                // redeem > 0 since supplied > _targetSupply
                redeemAmount = supplied.sub(_targetSupply);
            }
            _redeem(redeemAmount);
            _repay(redeemAmount);
            // supplied < _geSupplied(), by about 7 * 1e12 %
            supplied = supplied.sub(redeemAmount);
            // borrowed == _getBorrowed()
            borrowed = borrowed.sub(redeemAmount);
            i++;
        }
    }

    function deleverage(uint _targetSupply) external onlyAuthorized {
        _deleverage(_targetSupply);
    }

    // @dev Returns amount available for transfer
    function _withdraw(uint _amount) private returns (uint) {
        uint bal = token.balanceOf(address(this));
        if (_amount <= bal) {
            return _amount;
        }

        uint redeemAmount = _amount - bal;
        /*
        c = collateral ratio
        s = supplied
        b = borrowed
        r = amount to redeem
        x = amount to repay
        where
            r <= s - b (can't redeem more than unleveraged supply)
        and
            x <= b (can't repay more than borrowed)
        and
            (b - x) / (s - x - r) <= c (stay below c after redeem and repay)
        so pick x such that
            (b - cs + cr) / (1 - c) <= x <= b
        when b <= cs left side of equation above <= cr / (1 - c) so pick x such that
            cr / (1 - c) <= x <= b
        */
        uint supplied = _getSupplied();
        uint borrowed = _getBorrowed();
        uint marketCol = _getMarketCollateralRatio();
        uint safeCol = _getSafeCollateralRatio(marketCol);
        uint unleveraged = supplied.sub(borrowed);
        // r <= s - b
        if (redeemAmount > unleveraged) {
            redeemAmount = unleveraged;
        }
        // cr / (1 - c) <= x <= b
        uint repayAmount = redeemAmount.mul(safeCol).div(uint(1e18).sub(safeCol));
        if (repayAmount > borrowed) {
            repayAmount = borrowed;
        }

        _deleverage(supplied.sub(repayAmount));
        _redeem(redeemAmount);

        uint balAfter = token.balanceOf(address(this));
        if (balAfter < _amount) {
            return balAfter;
        }
        return _amount;
    }

    /*
    @notice Withdraw undelying token to vault
    @param _amount Amount of token to withdraw
    */
    function withdraw(uint _amount) external override onlyVault {
        require(_amount > 0, "withdraw = 0");
        // available <= _amount
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
        address _from,
        address _to,
        uint _amount
    ) private {
        // create dynamic array with 3 elements
        address[] memory path = new address[](3);
        path[0] = _from;
        path[1] = WETH;
        path[2] = _to;

        UniswapV2Router(dex).swapExactTokensForTokens(
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

        // claim COMP
        address[] memory cTokens = new address[](1);
        cTokens[0] = address(cToken);
        comptroller.claimComp(address(this), cTokens);

        uint compBal = comp.balanceOf(address(this));
        if (compBal > 0) {
            _swap(address(comp), address(token), compBal);
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
        // TODO: remove?
        // _supply() to decrease collateral ratio and earn interest
        // use _supply() instead of _deposit() to save gas
        uint bal = token.balanceOf(address(this));
        if (bal > 0) {
            _supply(bal);
        }
    }

    /*
    @notice Transfer token accidentally sent here to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(token), "protected token");
        require(_token != address(cToken), "protected token");
        require(_token != address(comp), "protected token");
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
