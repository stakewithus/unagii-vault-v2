// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.8.4;

// TODO: stable solidity version
// TODO: test

contract TimeLock {
  event SetNextAdmin(address nextAdmin);
  event AcceptAdmin(address admin);
  event SetDelay(uint256 delay);
  event Queue(
    bytes32 indexed txHash,
    address indexed target,
    uint256 value,
    bytes data,
    uint256 eta
  );
  event Execute(
    bytes32 indexed txHash,
    address indexed target,
    uint256 value,
    bytes data,
    uint256 eta
  );
  event Cancel(
    bytes32 indexed txHash,
    address indexed target,
    uint256 value,
    bytes data,
    uint256 eta
  );

  uint256 public constant GRACE_PERIOD = 14 days;
  uint256 public constant MIN_DELAY = 1 days;
  uint256 public constant MAX_DELAY = 30 days;

  address public admin;
  address public nextAdmin;
  uint256 public delay;

  mapping(bytes32 => bool) public queued;

  constructor(uint256 _delay) {
    admin = msg.sender;
    _setDelay(_delay);
  }

  receive() external payable {}

  modifier onlyAdmin() {
    require(msg.sender == admin, "!admin");
    _;
  }

  function setNextAdmin(address _nextAdmin) external onlyAdmin {
    nextAdmin = _nextAdmin;
    emit SetNextAdmin(_nextAdmin);
  }

  function acceptAdmin() external {
    require(msg.sender == nextAdmin, "!next admin");
    admin = msg.sender;
    emit AcceptAdmin(msg.sender);
  }

  function _setDelay(uint256 _delay) private {
    require(_delay >= MIN_DELAY, "delay < min");
    require(_delay <= MAX_DELAY, "delay > max");
    delay = _delay;

    emit SetDelay(delay);
  }

  /*
    @dev Only this contract can execute this function
    */
  function setDelay(uint256 _delay) external {
    require(msg.sender == address(this), "!timelock");

    _setDelay(_delay);
  }

  function _getTxHash(
    address target,
    uint256 value,
    bytes memory data,
    uint256 eta
  ) private pure returns (bytes32) {
    return keccak256(abi.encode(target, value, data, eta));
  }

  function getTxHash(
    address target,
    uint256 value,
    bytes calldata data,
    uint256 eta
  ) external pure returns (bytes32) {
    return _getTxHash(target, value, data, eta);
  }

  /*
    @notice Queue transaction
    @param target Address of contract or account to call
    @param value Ether value to send
    @param data Data to send to `target`
    @eta Execute Tx After. Time after which transaction can be executed.
    */
  function queue(
    address target,
    uint256 value,
    bytes calldata data,
    uint256 eta
  ) external onlyAdmin returns (bytes32) {
    require(eta >= block.timestamp + delay, "eta < now + delay");

    bytes32 txHash = _getTxHash(target, value, data, eta);
    queued[txHash] = true;

    emit Queue(txHash, target, value, data, eta);

    return txHash;
  }

  function execute(
    address target,
    uint256 value,
    bytes calldata data,
    uint256 eta
  ) external payable onlyAdmin returns (bytes memory) {
    bytes32 txHash = _getTxHash(target, value, data, eta);
    require(queued[txHash], "!queued");
    require(block.timestamp >= eta, "eta < now");
    require(block.timestamp <= eta + GRACE_PERIOD, "eta expired");

    queued[txHash] = false;

    // solium-disable-next-line security/no-call-value
    (bool success, bytes memory returnData) = target.call{ value: value }(data);
    require(success, "tx failed");

    emit Execute(txHash, target, value, data, eta);

    return returnData;
  }

  function cancel(
    address target,
    uint256 value,
    bytes calldata data,
    uint256 eta
  ) external onlyAdmin {
    bytes32 txHash = _getTxHash(target, value, data, eta);
    require(queued[txHash], "!queued");

    queued[txHash] = false;

    emit Cancel(txHash, target, value, data, eta);
  }
}
