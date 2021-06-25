// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 0.1.0

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "./interfaces/IFundManager.sol";

abstract contract Strategy {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    event SetNextTimeLock(address nextTimeLock);
    event AcceptTimeLock(address timeLock);
    event SetAdmin(address admin);
    event SetGuardian(address guardian);
    event SetWorker(address worker);
    event SetTreasury(address treasury);
    event SetFundManager(address fundManager);

    event Deposit(uint amount, uint borrowed);
    event Repay(uint amount, uint repaid);
    event Withdraw(uint amount, uint withdrawn);
    event Harvest(uint profit);
    event Skim(uint profit);
    event Report(uint gain, uint loss);

    // Privilege - time lock >= admin >= guardian >= worker >= treasury
    address public timeLock;
    address public nextTimeLock;
    address public admin;
    address public guardian;
    address public worker; // Bot that will calling deposit, repay, harvest, report
    address public treasury; // Profit from harvest is sent to this address

    IERC20 public immutable token;
    IFundManager public fundManager;

    // Performance fee sent to treasury when harvest()
    uint public perfFee = 1000;
    uint private constant PERF_FEE_CAP = 2000; // Upper limit to performance fee
    uint internal constant PERF_FEE_MAX = 10000;

    constructor(
        address _token,
        address _fundManager,
        address _guardian,
        address _worker,
        address _treasury
    ) {
        // Don't allow accidentally sending perf fee to 0 address
        require(_treasury != address(0), "treasury = 0 address");

        timeLock = msg.sender;
        admin = msg.sender;
        guardian = _guardian;
        worker = _worker;
        treasury = _treasury;

        require(
            IFundManager(_fundManager).token() == _token,
            "fund manager token != token"
        );

        fundManager = IFundManager(_fundManager);
        token = IERC20(_token);

        IERC20(_token).safeApprove(_fundManager, type(uint).max);
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
            msg.sender == timeLock ||
                msg.sender == admin ||
                msg.sender == guardian ||
                msg.sender == worker,
            "!auth"
        );
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
        emit AcceptTimeLock(msg.sender);
    }

    /*
    @notice Set admin
    @param _admin Address of admin
    */
    function setAdmin(address _admin) external onlyTimeLockOrAdmin {
        admin = _admin;
        emit SetAdmin(_admin);
    }

    /*
    @notice Set guardian
    @param _guardian Address of guardian
    */
    function setGuardian(address _guardian) external onlyTimeLockOrAdmin {
        guardian = _guardian;
        emit SetGuardian(_guardian);
    }

    /*
    @notice Set worker
    @param _worker Address of worker
    */
    function setWorker(address _worker) external onlyTimeLockOrAdmin {
        worker = _worker;
        emit SetWorker(_worker);
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
    @notice Set performance fee
    @param _fee Performance fee
    */
    function setPerfFee(uint _fee) external onlyTimeLockOrAdmin {
        require(_fee <= PERF_FEE_CAP, "fee > cap");
        perfFee = _fee;
    }

    function setFundManager(address _fundManager) external onlyTimeLock {
        if (address(fundManager) != address(0)) {
            token.safeApprove(address(fundManager), 0);
        }

        require(
            IFundManager(_fundManager).token() == address(token),
            "new fund manager token != token"
        );

        fundManager = IFundManager(_fundManager);
        token.safeApprove(_fundManager, type(uint).max);

        emit SetFundManager(_fundManager);
    }

    /*
    @notice Returns amount of token locked in this contract
    @dev Output may vary depending on price pulled from external DeFi contracts
    */
    function totalAssets() external view virtual returns (uint);

    /*
    @notice Deposit into strategy
    @param _amount Amount of token to deposit from fund manager
    @param _min Minimum amount borrowed
    */
    function deposit(uint _amount, uint _min) external virtual;

    /*
    @notice Repay fund manager
    @param _amount Amount of token to repay to fund manager
    @param _min Minimum amount repaid
    */
    function repay(uint _amount, uint _min) external virtual;

    /*
    @notice Withdraw token from this contract
    @dev Only callable by fund manager
    */
    function withdraw(uint _amount) external virtual;

    /*
    @notice Claim and sell rewards for token
    */
    function harvest() external virtual;

    /*
    @notice Free up any profit over debt
    */
    function skim() external virtual;

    /*
    @notice Report gain or loss back to fund manager
    @param _min Minimum value of total assets.
               Used to protect against price manipulation.
    @param _max Maximum value of total assets Used
               Used to protect against price manipulation.  
    */
    function report(uint _min, uint _max) external virtual;

    /*
    @notice Migrate to new version of this strategy
    @param _strategy Address of new strategy
    @dev Only callable by fund manager
    */
    function migrate(address _strategy) external virtual;

    /*
    @notice Transfer token accidentally sent here back to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external virtual;
}
