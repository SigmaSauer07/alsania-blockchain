package blockchain

import (
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"strings"
	"time"

	"github.com/ethereum/go-ethereum/rpc"
)

type AlsaniaBlockchain struct {
	Coin                AlsaniaCoin
	Nodes               map[string]struct{}
	Chain               []Block
	PalaConsensus       PaLaConsensus
	CurrentTransactions []Transaction
	PendingTransactions []Transaction
	Peers               []Peer
	Stakeholders        []string
	Contracts           map[string]Contract
	DeployedContracts   map[string]string
	IPFSVersion         string
	Web3                *rpc.Client
	PrivateKeyLength    int
	ValidCharacters     string
	MaxFutureBlockTime  int
	TransactionPool     TransactionPool
	Shards              map[string]Shard
}

func NewAlsaniaBlockchain() (*AlsaniaBlockchain, error) {
	web3, err := rpc.Dial("http://localhost:8545")
	if err != nil {
		return nil, err
	}

	ab := &AlsaniaBlockchain{
		Coin:                NewAlsaniaCoin(),
		Nodes:               make(map[string]struct{}),
		Chain:               []Block{},
		PalaConsensus:       NewPaLaConsensus([]Validator{}, NewTransactionPool(), []Block{}),
		Peers:               []Peer{},
		Stakeholders:        []string{},
		Contracts:           make(map[string]Contract),
		DeployedContracts:   make(map[string]string),
		IPFSVersion:         connectToIPFS(),
		Web3:                web3,
		PrivateKeyLength:    64,
		ValidCharacters:     "0123456789abcdef",
		MaxFutureBlockTime:  60,
		TransactionPool:     NewTransactionPool(),
		Shards:              make(map[string]Shard),
	}

	if ab.IPFSVersion != "" {
		fmt.Printf("Connected to IPFS daemon: %s\n", ab.IPFSVersion)
	}

	ab.createGenesisBlock()
	return ab, nil
}

func (ab *AlsaniaBlockchain) createGenesisBlock() {
	genesisBlock := NewBlock(0, []Transaction{}, "0")
	genesisBlock.Timestamp = time.Now().Unix()
	genesisBlock.Hash = genesisBlock.HashBlock()
	ab.Chain = append(ab.Chain, genesisBlock)
}

func (ab *AlsaniaBlockchain) AddNode(host string, port int) {
	ab.Nodes[fmt.Sprintf("%s:%d", host, port)] = struct{}{}
}

func (ab *AlsaniaBlockchain) AddPeer(host string, port int) {
	ab.Peers = append(ab.Peers, Peer{Host: host, Port: port})
}

func (ab *AlsaniaBlockchain) AddStakeholder(address string) {
	ab.Stakeholders = append(ab.Stakeholders, address)
}

func (ab *AlsaniaBlockchain) CreateTransaction(sender, recipient string, amount int, privateKey string) (Transaction, error) {
	transaction := Transaction{
		Sender:    sender,
		Recipient: recipient,
		Amount:    amount,
		Timestamp: time.Now().Unix(),
	}

	if privateKey != "" {
		signature, err := ab.Coin.SignTransaction(transaction, privateKey)
		if err != nil {
			return Transaction{}, err
		}
		transaction.Signature = signature
	}

	ab.TransactionPool.AddTransaction(transaction)
	return transaction, nil
}

func (ab *AlsaniaBlockchain) ValidateBlock(block Block) bool {
	calculatedMerkleRoot := block.CalculateMerkleRoot()
	return block.PreviousHash == ab.Chain[len(ab.Chain)-1].Hash &&
		strings.HasPrefix(block.Hash, "0") &&
		block.MerkleRoot == calculatedMerkleRoot &&
		ab.PalaConsensus.ValidateBlock(block, ab.Chain)
}

func (ab *AlsaniaBlockchain) ReachConsensus() {
	proposedBlock := ab.PalaConsensus.ProposeBlock()
	if proposedBlock != nil && ab.PalaConsensus.ValidateBlock(*proposedBlock, ab.Chain) {
		ab.AddBlockToChain(*proposedBlock)
		for _, peer := range ab.Peers {
			ab.SendBlockToPeer(peer.Host, peer.Port, *proposedBlock)
		}
	} else {
		fmt.Println("Proposed block failed validation, consensus not reached")
	}
}

func (ab *AlsaniaBlockchain) AddBlockToChain(block Block) error {
	if !ab.PalaConsensus.ValidateBlock(block, ab.Chain) {
		return errors.New("consensus validation failed")
	}
	if !ab.ValidateBlock(block) {
		return errors.New("block validation failed")
	}
	ab.Chain = append(ab.Chain, block)
	ab.TransactionPool.RemoveTransactions(block.Transactions)
	return nil
}

func (ab *AlsaniaBlockchain) SendBlockToPeer(host string, port int, block Block) error {
	conn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", host, port))
	if err != nil {
		return err
	}
	defer conn.Close()

	data, err := json.Marshal(block)
	if err != nil {
		return err
	}

	_, err = conn.Write(data)
	return err
}

func (ab *AlsaniaBlockchain) ReceiveBlockFromPeer(conn net.Conn) (Block, error) {
	defer conn.Close()

	var block Block
	decoder := json.NewDecoder(conn)
	err := decoder.Decode(&block)
	return block, err
}

func (ab *AlsaniaBlockchain) HandleTokenTransfer(transaction Transaction) (string, error) {
	err := ab.Coin.TransferToken(transaction.Sender, transaction.Recipient, transaction.Amount)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("Token transfer successful. Sender: %s, Recipient: %s, Amount: %d", transaction.Sender, transaction.Recipient, transaction.Amount), nil
}

func (ab *AlsaniaBlockchain) DeployContract(sender, contractName, contractCode string, gasLimit int) (string, error) {
	if _, exists := ab.DeployedContracts[contractName]; exists {
		return "", fmt.Errorf("contract with name '%s' already deployed", contractName)
	}

	// ...existing code for deploying contract...

	return contractAddress, nil
}

func (ab *AlsaniaBlockchain) InvokeContractMethod(sender, contractAddress, method string, args []interface{}, gasLimit int) error {
	// ...existing code for invoking contract method...
	return nil
}

func (ab *AlsaniaBlockchain) GetContractABI(contractAddress string) (string, error) {
	contract, exists := ab.Contracts[contractAddress]
	if !exists {
		return "", errors.New("ABI not found for the contract address")
	}
	return contract.ABI, nil
}

func (ab *AlsaniaBlockchain) TransferToken(tokenContractName, sender, recipient string, amount int, privateKey string) (string, error) {
	if _, exists := ab.DeployedContracts[tokenContractName]; !exists {
		return "", errors.New("token contract not deployed")
	}

	// ...existing code for transferring token...

	return fmt.Sprintf("Token transfer successful. Sender: %s, Recipient: %s, Amount: %d", sender, recipient, amount), nil
}

func (ab *AlsaniaBlockchain) GetTokenBalance(tokenContractName, address string) (int, error) {
	// ...existing code for getting token balance...
	return balance, nil
}

func (ab *AlsaniaBlockchain) HandleTokenEvent(event Event) {
	// ...existing code for handling token event...
}

func (ab *AlsaniaBlockchain) SendTransaction(transaction Transaction) {
	ab.Coin.AddPendingTransaction(transaction)
}

func (ab *AlsaniaBlockchain) GetBalanceFromBlockchain(tokenContractAddress, address string) (int, error) {
	// ...existing code for getting balance from blockchain...
	return balance, nil
}

func (ab *AlsaniaBlockchain) GetStakeholders() []string {
	stakeholders := []string{}
	for _, validator := range ab.PalaConsensus.Validators {
		stakeholders = append(stakeholders, validator.Address)
	}
	return stakeholders
}

func (ab *AlsaniaBlockchain) CreateShard(shardID string, validators []Validator) {
	ab.Shards[shardID] = NewShard(shardID, validators)
	ab.PalaConsensus.Validators = append(ab.PalaConsensus.Validators, validators...)
	ab.PalaConsensus.TotalStakedAmount = 0
	for _, v := range ab.PalaConsensus.Validators {
		ab.PalaConsensus.TotalStakedAmount += v.StakedAmount
	}
}

func (ab *AlsaniaBlockchain) GetShard(shardID string) (*Shard, error) {
	shard, exists := ab.Shards[shardID]
	if !exists {
		return nil, fmt.Errorf("shard with ID %s not found", shardID)
	}
	return &shard, nil
}

func (ab *AlsaniaBlockchain) SendTransactionToShard(shardID string, transaction Transaction) error {
	shard, err := ab.GetShard(shardID)
	if err != nil {
		return err
	}
	shard.AddTransaction(transaction)
	return nil
}

func (ab *AlsaniaBlockchain) ProcessShards() {
	for shardID, shard := range ab.Shards {
		for _, transaction := range shard.Transactions {
			ab.Coin.AddPendingTransaction(transaction)
		}
		shard.Transactions = []Transaction{}
	}
	ab.Coin.ProcessPendingTransactions()
}

func (ab *AlsaniaBlockchain) Run() {
	for {
		ab.Coin.ProcessPendingTransactions()
		ab.ReachConsensus()
		for _, peer := range ab.Peers {
			ab.SendBlockToPeer(peer.Host, peer.Port, ab.Chain[len(ab.Chain)-1])
		}
		time.Sleep(1 * time.Second)
	}
}
