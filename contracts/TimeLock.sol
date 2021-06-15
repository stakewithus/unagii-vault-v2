// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.8.4;

// TODO: stable solidity version
// TODO: comment
// TODO: gas optimize

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

    /*
    @notice Queue transaction
    @param target Address of contract or account to call
    @param value Ether value to send
    @param data Data to send to `target`
    @param _delay Time in seconds to wait after this tx
    @param nonce In case there is a need execute same tx multiple times
    */
    function queue(
        address target,
        uint value,
        bytes calldata data,
        uint _delay,
        uint nonce
    ) external onlyAdmin returns (bytes32) {
        require(_delay >= MIN_DELAY, "delay < min");

        // execute time after
        uint eta = block.timestamp + _delay;
        // tx hash may not be unique if eta is same
        bytes32 txHash = _getTxHash(target, value, data, eta, nonce);

        require(!queued[txHash], "queued");
        queued[txHash] = true;

        emit Log(txHash, target, value, data, eta, nonce, State.Queued);

        return txHash;
    }

    function execute(
        address target,
        uint value,
        bytes calldata data,
        uint eta,
        uint nonce
    ) external payable onlyAdmin returns (bytes memory) {
        bytes32 txHash = _getTxHash(target, value, data, eta, nonce);
        require(queued[txHash], "!queued");
        require(block.timestamp >= eta, "eta < now");
        require(block.timestamp <= eta + GRACE_PERIOD, "eta expired");

        queued[txHash] = false;

        // solium-disable-next-line security/no-call-value
        (bool success, bytes memory res) = target.call{value: value}(data);
        require(success, "tx failed");

        emit Log(txHash, target, value, data, eta, nonce, State.Executed);

        return res;
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
