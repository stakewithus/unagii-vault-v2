// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;
// TODO: solidity version

// version 1.0.0

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "../interfaces/IVault.sol";
import "./PerfFee.sol";
import "./Dex.sol";

abstract contract Strategy is PerfFee, Dex {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    event SetNextTimeLock(address nextTimeLock);
    event AcceptTimeLock(address timeLock);
    event SetAdmin(address admin);
    event Authorize(address addr, bool authorized);
    event SetTreasury(address treasury);
    event SetVault(address vault);

    // Privilege - time lock >= admin >= authorized addresses
    address public timeLock;
    address public nextTimeLock;
    address public admin;
    address public treasury; // Profit is sent to this address

    // authorization other than time lock and admin
    mapping(address => bool) public authorized;

    IERC20 public immutable token;
    IVault public vault;

    // TODO: worker, guardian?
    constructor(
        address _token,
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

        require(IVault(_vault).token() == _token, "vault token != token");

        vault = IVault(_vault);
        token = IERC20(_token);

        IERC20(_token).safeApprove(_vault, type(uint).max);
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
        if (address(vault) != address(0)) {
            token.safeApprove(address(vault), 0);
        }

        require(IVault(_vault).token() == address(token), "new vault token != token");

        vault = IVault(_vault);
        token.safeApprove(_vault, type(uint).max);

        emit SetVault(_vault);
    }

    /*
    @notice Returns approximate amount of token locked in this contract
    @dev Output may vary depending on price pulled from external DeFi contracts
    */
    function totalAssets() external view virtual returns (uint);

    /*
    @notice Deposit into strategy
    @param _amount Amount of token to deposit from vault
    @param _min Minimum amount borrowed
    */
    function deposit(uint _amount, uint _min) external virtual;

    /*
    @notice Withdraw token from this contract
    @dev Only vault can call
    */
    function withdraw(uint _amount) external virtual;

    /*
    @notice Repay vault
    @param _amount Amount of token to repay to vault
    @param _min Minimum amount repaid
    */
    function repay(uint _amount, uint _min) external virtual;

    /*
    @notice Claim rewards
    @param _minProfit Minumum amount of token to gain from selling rewards
    */
    function harvest(uint _minProfit) external virtual;

    /*
    @notice Transfer token accidentally sent here back to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external virtual;
}
