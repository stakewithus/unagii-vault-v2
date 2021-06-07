// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity ^0.8;

contract TestTimeLock {
  // test helper
  bytes public data;
  bool public fail;

  function callMe(bytes calldata _data) external {
    require(!fail, "failed");

    data = _data;
  }

  function setFail(bool _fail) external {
    fail = _fail;
  }
}
