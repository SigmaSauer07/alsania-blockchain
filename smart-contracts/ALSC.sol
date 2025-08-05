pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ALSC is ERC20, Ownable {
    uint256 public constant EMBER_CONVERSION_RATE = 10**18;
    
    // Track staked amounts for each user
    mapping(address => uint256) public stakedBalances;
    uint256 public totalStaked;
    
    // Events for transparency
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);

    constructor(uint256 initialSupply) ERC20("AlsaniaCoin", "ALSC") {
        _mint(msg.sender, initialSupply);
    }

    function stake(uint256 amount) public {
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        
        // Transfer tokens to contract instead of burning
        _transfer(msg.sender, address(this), amount);
        
        // Update staking records
        stakedBalances[msg.sender] += amount;
        totalStaked += amount;
        
        emit Staked(msg.sender, amount);
    }
    
    function unstake(uint256 amount) public {
        require(amount > 0, "Amount must be greater than 0");
        require(stakedBalances[msg.sender] >= amount, "Insufficient staked balance");
        
        // Update staking records
        stakedBalances[msg.sender] -= amount;
        totalStaked -= amount;
        
        // Return tokens to user
        _transfer(address(this), msg.sender, amount);
        
        emit Unstaked(msg.sender, amount);
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