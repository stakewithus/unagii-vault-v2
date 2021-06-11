// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity ^0.8;

contract TxTest {
    // test helper
    bytes public data;
    uint public value;
    bool public fail;

    fallback() external payable {}

    function test(bytes calldata _data) external payable {
        require(!fail, "failed");
        data = _data;
        value = msg.value;
    }

    function setFail(bool _fail) external {
        fail = _fail;
    }
}
