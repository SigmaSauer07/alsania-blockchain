require("@nomiclabs/hardhat-waffle");
require("@nomiclabs/hardhat-etherscan");

module.exports = {
  solidity: "0.8.4",
  networks: {
    hardhat: {},
    ropsten: {
      url: "https://ropsten.infura.io/v3/YOUR_INFURA_PROJECT_ID",
      accounts: [`0x${process.env.ROPSTEN_PRIVATE_KEY}`]
    }
  },
  etherscan: {
    apiKey: "YOUR_ETHERSCAN_API_KEY"
  }
};
