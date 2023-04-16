# unagii-vault-v2

![unagii-v2](./doc/unagii-v2.png)

### Install

```shell
# install virtualenv
python3 -m pip install --user virtualenv
virtualenv -p python3 venv
source venv/bin/activate

# install vyper
pip install vyper==0.2.12
pip install eth-brownie
pip install eth_account
pip install black
pip install blackadder
pip install slither-analyzer

brownie pm install OpenZeppelin/openzeppelin-contracts@3.4.0

cp .env.sample .env

# npm
npm i
```

### Test

```shell
brownie test tests/path-to-test-file-or-folder
```

### Mainnet Test

```shell
source .env

npx ganache-cli \
--fork https://mainnet.infura.io/v3/$WEB3_INFURA_PROJECT_ID \
--unlock $DAI_WHALE \
--unlock $USDC_WHALE \
--unlock $USDT_WHALE \
--unlock $WBTC_WHALE \
--networkId 999

env $(cat .env) brownie test tests/mainnet/test.py --network mainnet-fork -s

```

### Deploy

```shell
brownie accounts new dev

brownie run scripts/flat.py

env $(cat .env) brownie run scripts/script-to-run.py [function] --network ropsten
```

```javascript
{
  ropsten: {
    timeLock: "0x03ee26271C43B2AA2712F25f6e08E8419aAF5EAD",
    /*
    # TestToken
    0xfA4B8F893631814bF47E05a1a29d9d4365A90adD
    */
    uTest: "0x69c529Ec8e451D15c5EB394B3Edaca7304B7ff56",
    uEth: "0xDdC33E10f60EeC345440Dd49497b1dA38040bd54",
    testVault: "0x7905D4638DD6B23fcDFBE3e04fEBC911aD87Cde7",
    ethVault: "0xFaEeE4847AEE7a7eC48eb1BB3103E84FB7b4a0D1",
    testFundManager: "0xe9558bC2fC2d8203bFC467Ab67f7016c90400549",
    ethFundManager: "0x9Fb96bc1F352F26c0f624556ED39B65fa0a6Ac69",
    strategyTest0: "0x904a1698b721b4f10A0aC23Ff65BdB3673d7B152",
    strategyTest1: "0x446F3C16c87A5DdeD516D404121e7bB847748048",
    strategyTest2: "0x4C11CF6c73347Ae013E88dB97b4f285a8DE48322",
    strategyTest3: "0x88aBAB57C7b7f326294Bf86f63C8d41083F13924",
    strategyTest4: "0x65047f16e882BFD8F094c9edf1887346299AE2A9",
    strategyTest5: "0x3830336d04b5440e1e5F4aF8B610777087256881",
    strategyEthTest0: "0x77845D098a8a789F0A141dD7c9FB5204C1fe8e58",
    strategyEthTest1: "0x86dbA3AA9b04B2758555337AD58b61b4cA03ADd5",
    strategyEthTest2: "0xa46E8Ed416A8dccebAADf320529cBF46eBcf7995",
    strategyEthTest3: "0xE732303f7A2997D2ddE1bEBB6c30d3A7dac4f7cd",
    strategyEthTest4: "0x1133b7AA55fB87Af5dE48A6C908E6436d09F1644",
    strategyEthTest5: "0x4Da0f9627616951BD694fEc66e1A24715dB584b0",
  },
  mainnet: {
    timeLock: "0x6e8a1e3b0B59C029809eDEE5bb9dF96FF34812a9",
    uDai: "0x634b0273D7060313FAA60f96705116c9DE50fA1f",
    uUsdc: "0x49b09e7E434a3A4A924A3b640cBBA54bF93B5677",
    uUsdt: "0xBF8734c5A7b3e6D88aa0110beBB37844AC043d0A",
    uWbtc: "0x7F20551E082ba3E035F2890cBD1EC4E275b9C8C0",
    uEth: "0xDe07f45688cb6CfAaC398c1485860e186D55996D",
    daiVault: "0x9ce3018375d305CE3C3303A26eF62D3d2EB8561A",
    usdcVault: "0x7f75d72886D6A8677321E5602d18948aBCb4281A",
    usdtVault: "0x1Eb06EaE3263a35619dC87812a8e7Ec811B59E63",
    wbtcVault: "0xB088D7C71ea9eBAed981c103Fc3019B59950d2C9",
    ethVault: "0x8eF11c51a666C53Aeeec504f120cd1435E451342",
    daiFundManager: "0x7C765C474D231fd915dc78832b478F309071cba7",
    usdcFundManager: "0xb00AA15F78A278Be2FCb2aa7de899F3F863780f8",
    usdtFundManager: "0xdF60b2CC40AFd588Bf650977A2d6C6AF39939f4C",
    wbtcFundManager: "0x0349Cf57BaE5C0d9be56b9C478Ea3797c7BcFddB",
    ethFundManager: "0x9501B3a6DcE1Bbe6094356391F3992e08EE90E3a",
    // dai
    strategyCompLevDai: "0xbac5f0964006BD3871189dC0Da01E67d7C435C9F",
    strategyConvexAlUsdDai: "0x994cC3a3fC0e1cB9A16f5eD06Cf52169c09ab480",
    strategyConvexUsdpDai: "0x434d68Ffc1C4DaE115E2176EdDf6539A5b8ce7D9",
    // usdc
    strategyCompLevUsdc: "0x7bF9075D5e3FCD7819A978cF3E8Bb836aDBEf3E8",
    strategyConvexAlUsdUsdc: "0x159569426128deF2afBd3F5da5d230298f1D5Ab7",
    strategyConvexUsdpUsdc: "0x6250002E436fc3df09cB09D654A46270c4344345",
    // usdt
    strategyConvexAlUsdUsdt: "0x48424fb48C1d148B38A9d6f29D05aD09003c9Af0",
    strategyConvexUsdpUsdt: "0x20A00e85dE13a49f872c033d6E4ba30Ba6C4e5f5",
    // wbtc
    strategyConvexBbtcWbtc: "0x07dA6bBA8529FC564f930aB7cCb7d7abbe6Ff56b",
    // eth
    strategyConvexStEth: "0xe859231d5ef4051D300698B9D46C421de1D7D5e0",
    // dev //
    dev_timeLock: "",
    dev_uDai: "0xffd51A24C65CC6981F3A543320fDadaf57ffFD7A",
    dev_uUsdc: "0x8ae16964763Bab7D73c5ECEBe7A51E6827BaED66",
    dev_uUsdt: "0x91Ea2CEbB595677368B2D5aa373eE836f90E7269",
    dev_uWbtc: "0x7f880118123547EA36F20C56617db899B50Fd6eb",
    dev_uEth: "0x5a6170496aAEC8649B25ec0cd53e55bC38525B00",
    dev_daiVault: "0x55Ece7dC08f1950245102aD92968bDaE1b359A0a",
    dev_usdcVault: "0xa32b1c0703B80E7bF40D172CC86Da8C620024AE6",
    dev_usdtVault: "0x28bCDbB64Ab1193bfD3C993351A2859E531F7005",
    dev_wbtcVault: "0xe801F6b268F1D8586Dbc03cd93D3ed4b9508eB2c",
    dev_ethVault: "0x7F129B99d81e5ac772B24BFb6af2f71309851F4C",
    dev_daiFundManager: "0x8a90faDe80feadCDD595c4f3611eB1886c924b61",
    dev_usdcFundManager: "0xf01c9a51ff69fC2982156be9D558d56002328Fcc",
    dev_usdtFundManager: "0xBd998633af470836fEf1C0E6b5c0A0AC3E325C39",
    dev_wbtcFundManager: "0xd5A84Cbb69351c6991BA56CF78052f59092d404C",
    dev_ethFundManager: "0x09f15F979Bf1b0CC8c8a19ed2E2feFF8EdE60e54",
    // dai
    dev_strategyCompLevDai: "0xC1B8F4Ac6c4aF37bD5Fca280F27Db7b950872417",
    dev_strategyConvexAlUsdDai: "0x9c9462314607D4D1759a6F1563ABB6025b561d5B",
    dev_strategyConvexUsdpDai: "0x5E22A1De3593ffacACA6a11AEabe07f222314cEc",
    // usdc
    dev_strategyCompLevUsdc: "0x5EF8f1A715Cab61Ecf71FD307ccf40685868EF43",
    dev_strategyConvexAlUsdUsdc: "0x47629E022e1b345f52F695935cf28e6942aD3804",
    dev_strategyConvexUsdpUsdc: "0xA15EF9f3e3De3AcebFF5478C66eDD021D1f51BE2",
    // usdt
    dev_strategyConvexAlUsdUsdt: "0x4787b5c60cE2cB244A8421c703ccEeE4B9c04c92",
    dev_strategyConvexUsdpUsdt: "0xC43CB1557119C9d8526D6aB4db378F3D7a73Ef8B",
    // wbtc
    dev_strategyConvexBbtcWbtc: "0xe282b36BA5456Ab21DCD0B6921b92Da69B2019E6",
    // eth
    dev_strategyConvexStEth: "0x302Ef51E94360fE890336812B09dF3d22d1024E8",
  }
}
```

### Misc

```shell
# black format python
black --check --include "(tests|scripts)" .
# format vyper
blackadder --fast --include '\.vy$' contracts

# select solc compiler
solc-select install 0.8.4
solc-select use 0.8.4

# slither
slither contracts/Contract.sol

# check code size (max 2457 bytes)
brownie compile -s
```
