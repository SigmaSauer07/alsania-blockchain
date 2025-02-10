pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ALSC is ERC20, Ownable {
    uint256 public constant EMBER_CONVERSION_RATE = 10**18;

    constructor(uint256 initialSupply) ERC20("AlsaniaCoin", "ALSC") {
        _mint(msg.sender, initialSupply);
    }

    function stake(uint256 amount) public {
        _burn(msg.sender, amount);
        // Logic for staking
    }

    function vote(uint256 proposalId, bool support) public {
        // Logic for governance voting
    }

    function convertToEmbers(uint256 amount) public pure returns (uint256) {
        return amount * EMBER_CONVERSION_RATE;
    }

    function convertFromEmbers(uint256 embers) public pure returns (uint256) {
        return embers / EMBER_CONVERSION_RATE;
    }
}