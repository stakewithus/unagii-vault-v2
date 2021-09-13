// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

import "../interfaces/uniswap/UniswapV2Router.sol";

contract Dex {
    // TODO: use Uniswap v3?
    address private constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    function _swap(
        address _dex,
        address _tokenIn,
        address _tokenOut,
        uint _amount
    ) internal {
        // create dynamic array with 3 elements
        address[] memory path = new address[](3);
        path[0] = _tokenIn;
        path[1] = WETH;
        path[2] = _tokenOut;

        UniswapV2Router(_dex).swapExactTokensForTokens(
            _amount,
            1,
            path,
            address(this),
            block.timestamp
        );
    }

    function _swapToEth(
        address _dex,
        address _tokenIn,
        uint _amount
    ) internal {
        // create dynamic array with 2 elements
        address[] memory path = new address[](2);
        path[0] = _tokenIn;
        path[1] = WETH;

        UniswapV2Router(_dex).swapExactTokensForETH(
            _amount,
            1,
            path,
            address(this),
            block.timestamp
        );
    }
}
