pragma solidity 0.8.3;

// import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVault {
    function borrow(uint amount) external;
    function repay(uint amount) external;
    function report(uint profit, uint loss) external;
}

struct Strategy {
    uint debt;
    bool approved;
}

contract StrategySplit {
    event ApproveStrategy(address indexed strategy);
    event RevokeStrategy(address indexed strategy);
    event AddStrategyToQueue(address indexed strategy);
    event RemoveStrategyFromQueue(address indexed strategy);

    address public admin;
    address public nextAdmin;
    address public timeLock;
    address public keeper;
    address public guardian;
    address public vault;
    address public token;

    uint constant private MAX_STRATEGIES = 20;
    address[] public withdrawalQueue;
    mapping(address => Strategy) public strategies;
    uint public totalDebt;

    function setNextAdmin(address _nextAdmin) external {}
    function acceptAdmin() external {}

    function approveStrategy(address _strategy) external {}
    function revokeStrategy(address _strategy) external {}
    function addStrategyToQueue(address _strategy) external {}
    function removeStrategyFromQueue(address _strategy) external {}

    function totalAssets() external view returns (uint) {
        return 0;
        // return IERC20(token).balanceOf(address(this)) + totalDebt;
    }

    function deposit(uint _amount) external {}
    function withdraw(uint _amount) external {}
    function exit() external {}
    function sweep(address _token) external {}
}