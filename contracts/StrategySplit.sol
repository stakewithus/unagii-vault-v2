pragma solidity 0.8.3;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVault {
    function borrow(uint amount) external;
    function repay(uint amount) external;
    function report(uint profit, uint loss) external;
}

interface IStrategy {
    function split() external view returns (address);
    function token() external view returns (address);
}

struct Strategy {
    uint debt;
    bool approved;
    bool active;
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

    bool public forceExit;

    uint constant private MAX_STRATEGIES = 20;
    address[] public withdrawalQueue;
    mapping(address => Strategy) public strategies;
    uint public totalDebt;

    modifier onlyAdmin() {
        require(msg.sender == admin, "!admn");
        _;
    }

    modifier onlyTimeLock() {
        require(msg.sender == timeLock, "!time lock");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == admin || msg.sender == keeper || msg.sender == guardian, "!authorized");
        _;
    }

    modifier onlyActiveStrategy(address _strategy) {
        require(strategies[_strategy].active, "!active");
        _;
    }

    function approveStrategy(address _strategy) external onlyTimeLock {
        Strategy storage strategy = strategies[_strategy];
        require(!strategy.approved, "approved");
        require(IStrategy(_strategy).split() == address(this), "!strategy.split");
        require(IStrategy(_strategy).token() == token, "!strategy.token");

        strategy.approved = true;
        emit ApproveStrategy(_strategy);
    }

    function revokeStrategy(address _strategy) external onlyAdmin {
        Strategy storage strategy = strategies[_strategy];
        require(strategy.approved, "!approved");
        require(!strategy.active, "active");

        delete strategies[_strategy];
        emit RevokeStrategy(_strategy);
    }

    function addStrategyToQueue(address _strategy) external onlyAdmin {
        Strategy storage strategy = strategies[_strategy];
        require(strategy.approved, "!approved");
        require(!strategy.active, "active");
        require(withdrawalQueue.length < MAX_STRATEGIES, "active > max");

        withdrawalQueue.push(_strategy);
        strategy.active = true;

        emit AddStrategyToQueue(strategy);
    }

    function removeStrategyFromQueue(address _strategy) external onlyAdmin {
        Strategy storage strategy = strategies[_strategy];
        require(!strategy.active, "active");
        // TODO: require strategy is empty?

        strategy.active = false;

        for (uint i = 0; i < withdrawalQueue.length; i++) {
            if (withdrawalQueue[i] == _strategy) {
                /*
                if i == withdrawalQueue.length - 1
                    pop last element
                else i < withdrawalQueue.length - 1
                    shift elements to the left by one
                    pop last element
                */
                // here withdrawalQueue.length >= 1
                for (uint j = i; j < withdrawalQueue.length - 1; j++) {
                    withdrawalQueue[i] = withdrawalQueue[j + 1];
                }
                withdrawalQueue.pop();
                emit RemoveStrategyFromQueue(_strategy);
                return;
            }
        }
        revert("strategy not found");
    }

    function totalAssets() external view returns (uint) {
        return IERC20(token).balanceOf(address(this)) + totalDebt;
    }

    function deposit(uint _amount) external onlyAuthorized {
        uint diff = IERC20(token).balanceOf(address(this));
        IVault(vault).borrow(_amount);
        diff = IERC20(token).balanceof(address(this)) - diff;

        totalDebt += diff;
    }

    function withdraw(uint _amount) external onlyAuthorized {
        uint amount = _amount;
        
        uint bal = IERC20(token).balanceOf(address(this));
        if (amount > bal) {

        }
    }

    function borrow(uint amount) external;
    function repay(uint amount) external;
    function report(uint profit, uint loss) external;

    function exit() external onlyAuthorized {
        // for each strategy
            // withdraw all
    }

    function sweep(address _token) external onlyAdmin {}
}