// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.8.4;

// TODO: stable solidity version

contract TimeLock {
    enum State {
        Queued,
        Executed,
        Canceled
    }

    event SetNextAdmin(address nextAdmin);
    event AcceptAdmin(address admin);
    event Log(
        bytes32 indexed txHash,
        address indexed target,
        uint value,
        bytes data,
        uint eta,
        uint nonce,
        State state
    );

    uint private constant GRACE_PERIOD = 14 days;
    uint private constant MIN_DELAY = 1 days;
    uint private constant MAX_DELAY = 30 days;

    address public admin;
    address public nextAdmin;

    mapping(bytes32 => bool) public queued;

    constructor() {
        admin = msg.sender;
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

    function _getTxHash(
        address target,
        uint value,
        bytes memory data,
        uint eta,
        uint nonce
    ) private pure returns (bytes32) {
        return keccak256(abi.encode(target, value, data, eta, nonce));
    }

    function getTxHash(
        address target,
        uint value,
        bytes calldata data,
        uint eta,
        uint nonce
    ) external pure returns (bytes32) {
        return _getTxHash(target, value, data, eta, nonce);
    }

    function _queue(
        address target,
        uint value,
        bytes memory data,
        uint delay,
        uint nonce
    ) private {
        require(delay >= MIN_DELAY, "delay < min");

        // execute time after
        uint eta = block.timestamp + delay;
        // tx hash may not be unique if eta is same
        bytes32 txHash = _getTxHash(target, value, data, eta, nonce);

        require(!queued[txHash], "queued");
        queued[txHash] = true;

        emit Log(txHash, target, value, data, eta, nonce, State.Queued);
    }

    /*
    @notice Queue transaction
    @param target Address of contract or account to call
    @param value Ether value to send
    @param data Data to send to `target`
    @param delay Time in seconds to wait after this tx
    @param nonce In case there is a need execute same tx multiple times
    */
    function queue(
        address target,
        uint value,
        bytes calldata data,
        uint delay,
        uint nonce
    ) external onlyAdmin {
        _queue(target, value, data, delay, nonce);
    }

    function batchQueue(
        address[] calldata targets,
        uint[] calldata values,
        bytes[] calldata data,
        uint[] calldata delays,
        uint[] calldata nonces
    ) external onlyAdmin returns (bytes32[] memory) {
        require(targets.length > 0, "targets.length = 0");
        require(values.length == targets.length, "values.length != targets.length");
        require(data.length == targets.length, "data.length != targets.length");
        require(delays.length == targets.length, "delays.length != targets.length");
        require(nonces.length == targets.length, "nonces.length != targets.length");

        for (uint i = 0; i < targets.length; i++) {
            _queue(targets[i], values[i], data[i], delays[i], nonces[i]);
        }
    }

    function _execute(
        address target,
        uint value,
        bytes calldata data,
        uint eta,
        uint nonce
    ) private {
        bytes32 txHash = _getTxHash(target, value, data, eta, nonce);
        require(queued[txHash], "!queued");
        require(block.timestamp >= eta, "eta < now");
        require(block.timestamp <= eta + GRACE_PERIOD, "eta expired");

        queued[txHash] = false;

        // solium-disable-next-line security/no-call-value
        (bool success, ) = target.call{value: value}(data);
        require(success, "tx failed");

        emit Log(txHash, target, value, data, eta, nonce, State.Executed);
    }

    function execute(
        address target,
        uint value,
        bytes calldata data,
        uint eta,
        uint nonce
    ) external payable onlyAdmin {
        _execute(target, value, data, eta, nonce);
    }

    function batchExecute(
        address[] calldata targets,
        uint[] calldata values,
        bytes[] calldata data,
        uint[] calldata etas,
        uint[] calldata nonces
    ) external onlyAdmin returns (bytes32[] memory) {
        require(targets.length > 0, "targets.length = 0");
        require(values.length == targets.length, "values.length != targets.length");
        require(data.length == targets.length, "data.length != targets.length");
        require(etas.length == targets.length, "etas.length != targets.length");
        require(nonces.length == targets.length, "nonces.length != targets.length");

        for (uint i = 0; i < targets.length; i++) {
            _execute(targets[i], values[i], data[i], etas[i], nonces[i]);
        }
    }

    function cancel(
        address target,
        uint value,
        bytes calldata data,
        uint eta,
        uint nonce
    ) external onlyAdmin {
        bytes32 txHash = _getTxHash(target, value, data, eta, nonce);
        require(queued[txHash], "!queued");

        queued[txHash] = false;

        emit Log(txHash, target, value, data, eta, nonce, State.Canceled);
    }
}
