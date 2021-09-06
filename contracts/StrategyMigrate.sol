// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// migrate from v2 vaults to v3
import "./v2/V2Strategy.sol";

contract StrategyMigrate is V2Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    constructor(
        address _token,
        address _fundManager,
        address _treasury
    ) V2Strategy(_token, _fundManager, _treasury) {}

    function totalAssets() external view override returns (uint) {
        return token.balanceOf(address(this));
    }

    function deposit(uint _amount, uint _min) external override onlyAuthorized {
        uint borrowed = fundManager.borrow(_amount);
        require(borrowed >= _min, "borrowed < min");
    }

    function withdraw(uint _amount) external override onlyFundManager returns (uint) {
        token.transfer(address(fundManager), _amount);
        return 0;
    }

    function repay(uint _amount, uint _min) external override onlyAuthorized {
        uint repaid = fundManager.repay(_amount);
        require(repaid >= _min, "repaid < min");
    }

    function claimRewards(uint) external override {
        revert("no op");
    }

    function skim() external override {
        revert("no op");
    }

    function report(uint, uint) external override {
        revert("no op");
    }

    function harvest(
        uint,
        uint,
        uint
    ) external override {
        revert("no op");
    }

    function migrate(address _strategy) external override {
        revert("no op");
    }

    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(token), "protected token");
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }
}
