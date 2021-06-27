// SPDX-License-Identifier: AGPL-3.0-or-later
pragma solidity 0.7.6;

contract StrategyConvexUsdp {
    // using SafeERC20 for IERC20;
    // using SafeMath for uint;
    // address public constant booster =
    //     address(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    // address public constant cvx = address(0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B);
    // address public constant crv = address(0xD533a949740bb3306d119CC777fa900bA034cd52);
    // address public constant weth = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    // address public constant dai = address(0x6B175474E89094C44Da98b954EedeAC495271d0F);
    // address public constant usdc = address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    // address public constant usdt = address(0xdAC17F958D2ee523a2206206994597C13D831ec7);
    // address public constant uniswap =
    //     address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
    // address public constant sushiswap =
    //     address(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    // // DepositUsdp
    // // curve = 0x3c8cAee4E09296800f8D29A68Fa3837e2dae4940
    // // convex pool id
    // // id = 28
    // // reward = 0x24DfFd1949F888F91A0c8341Fc98a3F280a782a8;
    // /*
    //     (address _lp, , , address _reward, , ) = Booster(booster).poolInfo(id);
    //     require(_lp == address(want), "constructor: incorrect lp token");
    //     rewardContract = _reward;
    // */
    // // want = 3crv usdp
    // function balanceOfPool() public view returns (uint) {
    //     return Rewards(rewardContract).balanceOf(address(this));
    // }
    // function estimatedTotalAssets() public view override returns (uint) {
    //     return balanceOfWant().add(balanceOfPool());
    // }
    // // deposit
    // // Booster(booster).deposit(id, _want, true);
    // // withdraw
    // // Rewards(rewardContract).withdrawAndUnwrap(_amount, false);
    // /*
    // harvest
    //     Rewards(rewardContract).getReward(address(this), isClaimExtras);
    //     uint _crv = IERC20(crv).balanceOf(address(this));
    //     if (_crv > 0) {
    //         _crv = _adjustCRV(_crv);
    //         address[] memory path = new address[](3);
    //         path[0] = crv;
    //         path[1] = weth;
    //         path[2] = pathTarget[0];
    //         Uni(dex[0]).swapExactTokensForTokens(
    //             _crv,
    //             uint(0),
    //             path,
    //             address(this),
    //             now
    //         );
    //     }
    //     uint _cvx = IERC20(cvx).balanceOf(address(this));
    //     if (_cvx > 0) {
    //         address[] memory path = new address[](3);
    //         path[0] = cvx;
    //         path[1] = weth;
    //         path[2] = pathTarget[1];
    //         Uni(dex[1]).swapExactTokensForTokens(
    //             _cvx,
    //             uint(0),
    //             path,
    //             address(this),
    //             now
    //         );
    //     }
    //     uint _dai = IERC20(dai).balanceOf(address(this));
    //     uint _usdc = IERC20(usdc).balanceOf(address(this));
    //     uint _usdt = IERC20(usdt).balanceOf(address(this));
    //     if (_dai > 0 || _usdc > 0 || _usdt > 0) {
    //         ICurveFi(curve).add_liquidity([0, _dai, _usdc, _usdt], 0);
    //         def add_liquidity(_amounts: uint256[N_ALL_COINS], _min_mint_amount: uint256) -> uint256:
    //     }
    // */
}
