// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "../interfaces/unagii/IVaultV3.sol";
import "../Strategy.sol";

contract StrategyVaultV3 is Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    IVaultV3 public immutable V3;

    uint16 public slip = 950;
    uint16 public constant SLIP_BASIS = 1000;

    constructor(
        address _token,
        address _fundManager,
        address _treasury,
        IVaultV3 _V3
    ) Strategy(_token, _fundManager, _treasury) {
        require(_token == address(_V3.asset()), "token != asset");
        V3 = _V3;
    }

    function totalAssets() public view override returns (uint) {
        return
            token.balanceOf(address(this)) +
            V3.previewRedeem(V3.balanceOf(address(this)));
    }

    function deposit(uint256 _amount, uint256 _min) external override onlyAuthorized {
        require(_amount > 0, "deposit = 0");

        uint256 borrowed = fundManager.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");

        uint256 balance = token.balanceOf(address(this));
        require(balance > 0, "balance = 0");

        _checkApproval(token, address(V3), _amount);
        V3.deposit(balance, address(this));
    }

    function _withdraw(uint256 _amount) private returns (uint256 available) {
        // first, check from balance
        uint256 bal = token.balanceOf(address(this));
        if (bal >= _amount) return _amount;

        uint256 total = totalAssets();
        _amount = _amount > total ? total : _amount;

        // how much to withdraw from v3
        uint256 need = _amount - bal;

        uint256 shares = V3.previewWithdraw(need);
        uint256 received = V3.safeRedeem(
            shares,
            address(this),
            address(this),
            need.mul(slip).div(SLIP_BASIS)
        );

        return bal + received;
    }

    function withdraw(
        uint256 _amount
    ) external override onlyFundManager returns (uint256 loss) {
        require(_amount > 0, "withdraw = 0");

        uint256 available = _withdraw(_amount);
        uint256 debt = fundManager.getDebt(address(this));

        uint256 total = totalAssets();
        if (debt > total) loss = debt - total;

        if (available > 0) token.safeTransfer(msg.sender, available);
        emit Withdraw(_amount, available, loss);
    }

    function repay(uint256 _amount, uint256 _min) external override onlyAuthorized {
        require(_amount > 0, "repay = 0");
        uint256 available = _withdraw(_amount);
        uint256 repaid = fundManager.repay(available);
        require(repaid >= _min, "repaid < min");

        emit Repay(_amount, repaid);
    }

    /// nothing as compounding is handled in v3
    function claimRewards(uint256 _minProfit) external override onlyAuthorized {}

    function _skim() private {
        uint256 total = totalAssets();
        uint256 debt = fundManager.getDebt(address(this));
        require(total > debt, "total <= debt");

        uint256 profit = total - debt;
        // reassign to actual amount withdrawn
        profit = _withdraw(profit);

        emit Skim(total, debt, profit);
    }

    function skim() external override onlyAuthorized {
        _skim();
    }

    function _report(uint256 _minTotal, uint256 _maxTotal) private {
        uint256 total = totalAssets();
        require(total >= _minTotal, "total < min");
        require(total <= _maxTotal, "total > max");

        uint256 gain = 0;
        uint256 loss = 0;
        uint256 free = 0; // balance of token
        uint256 debt = fundManager.getDebt(address(this));
        if (total > debt) {
            gain = total - debt;

            free = token.balanceOf(address(this));
            if (gain > free) {
                gain = free;
            }
        } else {
            loss = debt - total;
        }

        if (gain > 0 || loss > 0) {
            fundManager.report(gain, loss);
        }

        emit Report(gain, loss, free, total, debt);
    }

    function report(
        uint256 _minTotal,
        uint256 _maxTotal
    ) external override onlyAuthorized {
        _report(_minTotal, _maxTotal);
    }

    function harvest(
        uint256 _minProfit,
        uint256 _minTotal,
        uint256 _maxTotal
    ) external override onlyAuthorized {
        _skim();
        _report(_minTotal, _maxTotal);
    }

    function migrate(address _strategy) external override onlyFundManager {
        Strategy strat = Strategy(_strategy);
        require(address(strat.token()) == address(token), "strategy token != token");
        require(
            address(strat.fundManager()) == address(fundManager),
            "strategy fund manager != fund manager"
        );

        uint256 bal = _withdraw(type(uint).max);
        token.safeApprove(_strategy, bal);
        strat.transferTokenFrom(address(this), bal);
    }

    /*
    @notice Transfer token accidentally sent here to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(token), "protected token");
        require(_token != address(V3), "protected token");
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }

    function setSlip(uint16 _slip) external onlyAuthorized {
        require(_slip <= SLIP_BASIS, "slip > max");
        slip = _slip;
    }

    function _checkApproval(IERC20 _token, address _spender, uint256 _amount) internal {
        uint256 approval = _token.allowance(address(this), _spender);
        if (approval > _amount) return;
        _token.safeApprove(_spender, 0);
        _token.safeApprove(_spender, type(uint256).max);
    }
}
