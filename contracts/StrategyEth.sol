// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

// version 0.1.0

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "./interfaces/IEthFundManager.sol";

abstract contract StrategyEth {
    using SafeERC20 for IERC20;
    using SafeMath for uint;

    event SetNextTimeLock(address nextTimeLock);
    event AcceptTimeLock(address timeLock);
    event SetAdmin(address admin);
    event Authorize(address addr, bool authorized);
    event SetTreasury(address treasury);
    event SetFundManager(address fundManager);

    event ReceiveEth(address indexed sender, uint amount);
    event Deposit(uint amount, uint borrowed);
    event Repay(uint amount, uint repaid);
    event Withdraw(uint amount, uint withdrawn, uint loss);
    event ClaimRewards(uint profit);
    event Skim(uint total, uint debt, uint profit);
    event Report(uint gain, uint loss, uint free, uint total, uint debt);

    // Privilege - time lock >= admin >= authorized addresses
    address public timeLock;
    address public nextTimeLock;
    address public admin;
    address public treasury; // Profit is sent to this address

    // authorization other than time lock and admin
    mapping(address => bool) public authorized;

    address internal constant ETH = 0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE;
    address public constant token = ETH;
    IEthFundManager public fundManager;

    // Performance fee sent to treasury
    uint public perfFee = 1000;
    uint private constant PERF_FEE_CAP = 2000; // Upper limit to performance fee
    uint internal constant PERF_FEE_MAX = 10000;

    bool public claimRewardsOnMigrate = true;

    constructor(address _fundManager, address _treasury) {
        // Don't allow accidentally sending perf fee to 0 address
        require(_treasury != address(0), "treasury = 0 address");

        timeLock = msg.sender;
        admin = msg.sender;
        treasury = _treasury;

        require(
            IEthFundManager(_fundManager).token() == ETH,
            "fund manager token != ETH"
        );

        fundManager = IEthFundManager(_fundManager);
    }

    receive() external payable {
        emit ReceiveEth(msg.sender, msg.value);
    }

    function _sendEth(address _to, uint _amount) internal {
        require(_to != address(0), "to = 0 address");
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

    modifier onlyFundManager() {
        require(msg.sender == address(fundManager), "!fund manager");
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
        require(_admin != address(0), "admin = 0 address");
        admin = _admin;
        emit SetAdmin(_admin);
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
        require(
            IEthFundManager(_fundManager).token() == ETH,
            "new fund manager token != ETH"
        );

        fundManager = IEthFundManager(_fundManager);

        emit SetFundManager(_fundManager);
    }

    /*
    @notice Set `claimRewardsOnMigrate`. If `false` skip call to `claimRewards`
            when `migrate` is called.
    @param _claimRewards Boolean to call or skip call to `claimRewards`
    */
    function setClaimRewardsOnMigrate(bool _claimRewards) external onlyTimeLockOrAdmin {
        claimRewardsOnMigrate = _claimRewards;
    }

    /*
    @notice Returns approximate amount of ETH locked in this contract
    @dev Output may vary depending on price pulled from external DeFi contracts
    */
    function totalAssets() external view virtual returns (uint);

    /*
    @notice Deposit into strategy
    @param _amount Amount of ETH to deposit from fund manager
    @param _min Minimum amount borrowed
    */
    function deposit(uint _amount, uint _min) external virtual;

    /*
    @notice Withdraw ETH from this contract
    @dev Only callable by fund manager
    @dev Returns current loss = debt to fund manager - total assets
    */
    function withdraw(uint _amount) external virtual returns (uint);

    /*
    @notice Repay fund manager
    @param _amount Amount of ETH to repay to fund manager
    @param _min Minimum amount repaid
    @dev Call report after this to report any loss
    */
    function repay(uint _amount, uint _min) external virtual;

    /*
    @notice Claim any reward tokens, sell for ETH
    @param _minProfit Minumum amount of ETH to gain from selling rewards
    */
    function claimRewards(uint _minProfit) external virtual;

    /*
    @notice Free up any profit over debt
    */
    function skim() external virtual;

    /*
    @notice Report gain or loss back to fund manager
    @param _minTotal Minimum value of total assets.
               Used to protect against price manipulation.
    @param _maxTotal Maximum value of total assets Used
               Used to protect against price manipulation.  
    */
    function report(uint _minTotal, uint _maxTotal) external virtual;

    /*
    @notice Claim rewards, skim and report
    @param _minProfit Minumum amount of ETH to gain from selling rewards
    @param _minTotal Minimum value of total assets.
               Used to protect against price manipulation.
    @param _maxTotal Maximum value of total assets Used
               Used to protect against price manipulation.  
    */
    function harvest(
        uint _minProfit,
        uint _minTotal,
        uint _maxTotal
    ) external virtual;

    /*
    @notice Migrate to new version of this strategy
    @param _strategy Address of new strategy
    @dev Only callable by fund manager
    */
    function migrate(address payable _strategy) external virtual;

    /*
    @notice Transfer token accidentally sent here back to admin
    @param _token Address of token to transfer
    */
    function sweep(address _token) external virtual;
}
