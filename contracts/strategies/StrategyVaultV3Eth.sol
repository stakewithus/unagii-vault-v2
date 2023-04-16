// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "../interfaces/unagii/IVaultV3.sol";
import "../interfaces/IWETH.sol";
import "../StrategyEth.sol";

contract StrategyVaultV3Eth is StrategyEth {
    using SafeERC20 for IERC20;
    using SafeMath for uint256;

    IVaultV3 public constant V3 = IVaultV3(0x6aBE5f87E3F4dC87301064F63CA5b244d119980d);
    IWETH public constant WETH9 = IWETH(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);

    uint16 public slip = 0;
    uint16 public constant SLIP_BASIS = 1000;

    constructor(
        address _fundManager,
        address _treasury
    ) StrategyEth(_fundManager, _treasury) {}

    function totalAssets() public view override returns (uint) {
        return V3.previewRedeem(V3.balanceOf(address(this))) + address(this).balance;
    }

    function deposit(uint256 _amount, uint256 _min) external override onlyAuthorized {
        require(_amount > 0, "deposit = 0");

        uint256 borrowed = fundManager.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");

        uint256 balance = address(this).balance;
        require(balance > 0, "balance = 0");

        // wrap ETH to WETH
        WETH9.deposit{value: balance}();

        _checkApproval(WETH9, address(V3), _amount);
        V3.deposit(balance, address(this));
    }

    function _withdraw(uint256 _amount) private returns (uint256 available) {
        // first, check from ETH balance
        uint256 bal = address(this).balance;
        if (bal >= _amount) return _amount;

        uint256 total = totalAssets();
        if (_amount > total) _amount = total;

        // how much to withdraw from v3
        uint256 need = _amount - bal;

        uint256 shares = V3.previewWithdraw(need);
        uint256 received = V3.safeRedeem(
            shares,
            address(this),
            address(this),
            need.mul(slip).div(SLIP_BASIS)
        );

        // unwrap WETH to ETH
        WETH9.withdraw(received);

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

        if (available > 0) _sendEth(msg.sender, available);
        emit Withdraw(_amount, available, loss);
    }

    function repay(uint256 _amount, uint256 _min) external override onlyAuthorized {
        require(_amount > 0, "repay = 0");
        uint256 available = _withdraw(_amount);
        uint256 repaid = fundManager.repay{value: available}(available);
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
        uint256 free = 0; // balance of ETH
        uint256 debt = fundManager.getDebt(address(this));
        if (total > debt) {
            gain = total - debt;

            free = address(this).balance;
            if (gain > free) {
                gain = free;
            }
        } else {
            loss = debt - total;
        }

        if (gain > 0 || loss > 0) {
            fundManager.report{value: gain}(gain, loss);
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

    function migrate(address payable _strategy) external override onlyFundManager {
        StrategyEth strat = StrategyEth(_strategy);
        require(address(strat.token()) == ETH, "strategy token != ETH");
        require(
            address(strat.fundManager()) == address(fundManager),
            "strategy fund manager != fund manager"
        );

        uint bal = _withdraw(type(uint).max);
        // WARNING: may lose all ETH if sent to wrong address
        _sendEth(address(strat), bal);
    }

    /*
    @notice Transfer token accidentally sent here to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(WETH9), "protected token");
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
