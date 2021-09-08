// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// contract to migrate from v2 to v3 vault
import "./v2/V2Strategy.sol";

interface IV2Vault {
    function paused() external view returns (bool);

    function token() external view returns (address);

    function uToken() external view returns (address);

    function totalAssets() external view returns (uint);

    function debt() external view returns (uint);

    function calcMaxBorrow() external view returns (uint);
}

interface IV3Vault {
    function paused() external view returns (bool);

    function token() external view returns (address);

    function uToken() external view returns (address);
}

interface IUnagiiToken {
    function minter() external view returns (address);
}

contract StrategyMigrate is V2Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    IV2Vault public v2;
    IV3Vault public v3;

    constructor(
        address _token,
        address _fundManager,
        address _treasury,
        address _v2,
        address _v3
    ) V2Strategy(_token, _fundManager, _treasury) {
        require(_v2 != _v3, "v2 = v3");

        v2 = IV2Vault(_v2);
        v3 = IV3Vault(_v3);

        require(v2.token() == _token, "v2 token != token");
        require(v3.token() == _token, "v3 token != token");

        require(v2.uToken() == v3.uToken(), "v2 uToken != v3 uToken");
    }

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

    function migrate(address) external override {
        revert("no op");
    }

    function sweep(address _token) external override onlyAuthorized {
        require(_token != address(token), "protected token");
        IERC20(_token).safeTransfer(admin, IERC20(_token).balanceOf(address(this)));
    }

    /*
    Migrate from V2 to V3 vault

    t = token
    ut = unagii token
    v2 = v2 vault
    v3 = v3 vault
    f = fund manager
    s = this mcontract

    action | caller
    --------------------------
    v3.setPause(true) | admin

    # activate this strategy
    f approve this contract | time lock
    f activate this contract | admin
    f withdraw from all strategies | admin
    f remove all strategies from queue except this contract | admin
    --------------------------
    v2.setMinReserve(0) | admin
    --------------------------
    # transfer funds from v2 to fund manager
    f.borrowFromVault(MAX_UINT, token.balanceOf(v2)) | time lock
    --------------------------
    v2.setPause(true) | time lock

    # checks right before migration
    v3.paused() == true
    v2.paused() == true

    ut.minter() == v2

    token.balanceOf(v2) == 0
    token.balanceOf(f) >= v2.debt()
    f.calcMaxBorrow(s) == token.balanceOf(f)

    # transfer funds from V2 to V3
    s.migrateToV3() | time lock

    # checks right after migration
    token.balanceOf(v2) == 0
    token.balanceOf(f) == 0
    token.balanceOf(s) == 0
    token.balanceOf(v3) >= balance of fund manager before transfer
    --------------------------
    ut.setMinter(v3) | time lock
    */

    function _checkBefore() private view {
        require(v2.paused(), "v2 not paused");
        require(v3.paused(), "v3 not paused");

        // check v3 is not initialized, uToken minter is still v2
        require(IUnagiiToken(v2.uToken()).minter() == address(v2), "v2 != minter");

        // check fund manager has borrowed everything in v2
        require(token.balanceOf(address(v2)) == 0, "v2 balance > 0");
        uint bal = token.balanceOf((address(fundManager)));
        require(bal >= v2.debt(), "fund manager balance < debt");

        // check this contract can borrow everything from fund manager
        require(
            bal == fundManager.calcMaxBorrow(address(this)),
            "fund manager balance != max borrow"
        );
    }

    function migrateToV3() external onlyTimeLock {
        _checkBefore();

        // borrow all from fund manager
        uint bal = token.balanceOf(address(fundManager));
        uint borrowed = fundManager.borrow(bal);
        require(borrowed >= bal, "borrowed < min");

        // transfer to V3
        token.safeTransfer(address(v3), token.balanceOf(address(this)));

        _checkAfter(bal);
    }

    function _checkAfter(uint _balBefore) private view {
        require(token.balanceOf(address(v2)) == 0, "v2 balance > 0");
        require(token.balanceOf(address(fundManager)) == 0, "fund manager balance > 0");
        require(token.balanceOf(address(this)) == 0, "balance > 0");
        require(token.balanceOf(address(v3)) >= _balBefore, "v3 balance != v2 balance");
    }
}
