// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVaultV3 is IERC20 {
    event Deposit(
        address indexed caller,
        address indexed owner,
        uint256 assets,
        uint256 shares
    );

    event Withdraw(
        address indexed caller,
        address indexed receiver,
        address indexed owner,
        uint256 assets,
        uint256 shares
    );

    function owner() external view returns (address);

    function asset() external view returns (IERC20);

    function totalAssets() external view returns (uint256 assets);

    function convertToShares(uint256 assets) external view returns (uint256 shares);

    function convertToAssets(uint256 shares) external view returns (uint256 assets);

    function maxDeposit(address receiver) external view returns (uint256 assets);

    function previewDeposit(uint256 assets) external view returns (uint256 shares);

    function deposit(
        uint256 assets,
        address receiver
    ) external returns (uint256 shares);

    function maxMint(address receiver) external view returns (uint256 shares);

    function previewMint(uint256 shares) external view returns (uint256 assets);

    function mint(uint256 shares, address receiver) external returns (uint256 assets);

    function maxWithdraw(address owner) external view returns (uint256 assets);

    function previewWithdraw(uint256 assets) external view returns (uint256 shares);

    function withdraw(
        uint256 assets,
        address receiver,
        address owner
    ) external returns (uint256 shares);

    function maxRedeem(address owner) external view returns (uint256 shares);

    function previewRedeem(uint256 shares) external view returns (uint256 assets);

    function redeem(
        uint256 shares,
        address receiver,
        address owner
    ) external returns (uint256 assets);

    function safeRedeem(
        uint256 shares,
        address receiver,
        address owner,
        uint256 minAssets
    ) external returns (uint256 assets);

    function setBlockDelay(uint8) external;
}
