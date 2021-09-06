// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: solidity version

// version 3.0.0

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "../interfaces/IEthVault.sol";
import "./PerfFee.sol";
import "./Dex.sol";

abstract contract StrategyEth is PerfFee, Dex {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    event SetNextTimeLock(address nextTimeLock);
    event AcceptTimeLock(address timeLock);
    event SetAdmin(address admin);
    event Authorize(address addr, bool authorized);
    event SetTreasury(address treasury);
    event SetVault(address vault);

    event ReceiveEth(address indexed sender, uint amount);

    // Privilege - time lock >= admin >= authorized addresses
    address public timeLock;
    address public nextTimeLock;
    address public admin;
    address public treasury; // Profit is sent to this address

    // authorization other than time lock and admin
    mapping(address => bool) public authorized;

    address internal constant ETH = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE;
    address public constant token = ETH;
    IEthVault public vault;

    constructor(
        address _vault,
        address _treasury,
        uint _minProfit,
        uint _maxProfit
    ) {
        // Don't allow accidentally sending perf fee to 0 address
        require(_treasury != address(0), "treasury = 0 address");

        timeLock = msg.sender;
        admin = msg.sender;
        treasury = _treasury;

        _setMinMaxProfit(_minProfit, _maxProfit);

        require(IEthVault(_vault).token() == ETH, "fund manager token != ETH");

        vault = IEthVault(_vault);
    }

    receive() external payable {
        emit ReceiveEth(msg.sender, msg.value);
    }

    function _sendEth(address _to, uint _amount) internal {
        require(_to != address(0), "to = zero address");
        (bool sent, ) = _to.call{value: _amount}("");
        require(sent, "Send ETH failed");
    }

    modifier onlyTimeLock() {
        require(msg.sender == timeLock, "!time lock");
        _;
    }

    modifier onlyTimeLockOrAdmin() {
        require(msg.sender == timeLock || msg.sender == admin, "!auth");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == timeLock || msg.sender == admin || authorized[msg.sender],
            "!auth"
        );
        _;
    }

    modifier onlyVault() {
        require(msg.sender == address(vault), "!vault");
        _;
    }

    /*
    @notice Set next time lock
    @param _nextTimeLock Address of next time lock
    @dev nextTimeLock can become timeLock by calling acceptTimeLock()
    */
    function setNextTimeLock(address _nextTimeLock) external onlyTimeLock {
        // Allow next time lock to be zero address (cancel next time lock)
        nextTimeLock = _nextTimeLock;
        emit SetNextTimeLock(_nextTimeLock);
    }

    /*
    @notice Set timeLock to msg.sender
    @dev msg.sender must be nextTimeLock
    */
    function acceptTimeLock() external {
        require(msg.sender == nextTimeLock, "!next time lock");
        timeLock = msg.sender;
        nextTimeLock = address(0);
        emit AcceptTimeLock(msg.sender);
    }

    /*
    @notice Set admin
    @param _admin Address of admin
    */
    function setAdmin(address _admin) external onlyTimeLockOrAdmin {
        require(_admin != address(0), "admin = 0 address");
        admin = _admin;
        emit SetAdmin(_admin);
    }

    /*
    @notice Set treasury
    @param _treasury Address of treasury
    */
    function setTreasury(address _treasury) external onlyTimeLockOrAdmin {
        // Don't allow accidentally sending perf fee to 0 address
        require(_treasury != address(0), "treasury = 0 address");
        treasury = _treasury;
        emit SetTreasury(_treasury);
    }

    /*
    @notice Set authorization
    @param _addr Address to authorize
    @param _authorized Boolean
    */
    function authorize(address _addr, bool _authorized) external onlyTimeLockOrAdmin {
        require(_addr != address(0), "addr = 0 address");
        authorized[_addr] = _authorized;
        emit Authorize(_addr, _authorized);
    }

    function setMinMaxProfit(uint _minProfit, uint _maxProfit)
        external
        onlyTimeLockOrAdmin
    {
        _setMinMaxProfit(_minProfit, _maxProfit);
    }

    /*
    @notice Set vault
    @param _vault Address of vault
    */
    function setVault(address _vault) external onlyTimeLock {
        require(IEthVault(_vault).token() == ETH, "new vault token != ETH");

        vault = IEthVault(_vault);

        emit SetVault(_vault);
    }

    function _totalAssets() internal view virtual returns (uint);

    /*
    @notice Returns approximate amount of ETH locked in this contract
    @dev Output may vary depending on price pulled from external DeFi contracts
    */
    function totalAssets() external view returns (uint) {
        return _totalAssets();
    }

    /*
    @dev Deposit all ETH into strategy
    */
    function _deposit() internal virtual;

    /*
    @notice Borrow from vault and deposit into strategy
    @param _amount Amount of ETH to borrow from vault
    @param _min Minimum amount borrowed
    */
    function deposit(uint _amount, uint _min) external onlyAuthorized {
        if (_amount > 0) {
            uint borrowed = vault.borrow(_amount);
            require(borrowed >= _min, "borrowed < min");
        }
        _deposit();
    }

    /*
    @dev Withdraw from strategy
    */
    function _withdraw(uint _amount) internal virtual;

    /*
    @notice Withdraw ETH from this contract
    @dev Only vault can call
    */
    function withdraw(uint _amount) external onlyVault {
        require(_amount > 0, "withdraw = 0");

        _withdraw(_amount);

        uint bal = address(this).balance;
        if (bal < _amount) {
            _amount = bal;
        }
        if (_amount > 0) {
            _sendEth(msg.sender, _amount);
        }
    }

    /*
    @notice Repay vault
    @param _amount Amount of ETH to repay to vault
    @param _min Minimum amount repaid
    */
    function repay(uint _amount, uint _min) external onlyAuthorized {
        require(_amount > 0, "repay = 0");

        _withdraw(_amount);

        uint bal = address(this).balance;
        if (bal < _amount) {
            _amount = bal;
        }

        uint repaid = vault.repay{value: _amount}();
        require(repaid >= _min, "repaid < min");
    }

    function _harvest(uint _minProfit) internal virtual;

    /*
    @notice Claim rewards
    @param _minProfit Minumum amount of ETH to gain from selling rewards
    @dev Call internal harvest to guarantee that only authorized account can
         call this function
    */
    function harvest(uint _minProfit) external onlyAuthorized {
        _harvest(_minProfit);
    }

    /*
    @notice Transfer token accidentally sent here back to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external virtual;
}
