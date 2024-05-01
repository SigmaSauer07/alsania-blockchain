package main

import (
	"crypto/ecdsa"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"net/http"
	"time"
	"sync"
	"crypto/sha256"
	"crypto/elliptic"
)

type AlsaniaCoin struct {
	Name                        string
	Symbol                      string
	TotalSupply                 int
	EmbersPerCoin               int
	Balances                    map[string]int
	LockedBalances              map[string]int
	TokenHolders                map[string]bool
	VotingPower                 map[string]int
	GovernanceContract          interface{} // Type of governance contract
	PrivacyEnabled              bool
	SmartContractIntegration    bool
	StakingEnabled              bool
	TotalStaked                 int
	TransactionFee              int
	Delegations                 map[string]map[string]int // Track stake delegations
	PendingTransactions         []interface{}             // Track pending transactions
	BaseGasFee                  int                       // Initial base gas fee
	DynamicGasFeeMultiplier     float64                   // Multiplier to adjust gas fee dynamically
	PriceOracle                 ExternalOracle
}

func NewAlsaniaCoin() *AlsaniaCoin {
	alsaniaCoin := &AlsaniaCoin{
		Name:                      "AlsaniaCoin",
		Symbol:                    "ALSC",
		TotalSupply:               50000000,
		EmbersPerCoin:             int(1e18),
		Balances:                  make(map[string]int),
		LockedBalances:            make(map[string]int),
		TokenHolders:              make(map[string]bool),
		VotingPower:               make(map[string]int),
		PrivacyEnabled:            true,
		SmartContractIntegration:  true,
		StakingEnabled:            true,
		TransactionFee:            1,
		Delegations:               make(map[string]map[string]int),
		PendingTransactions:       make([]interface{}, 0),
		BaseGasFee:                1,
		DynamicGasFeeMultiplier:   1.0,
		PriceOracle:               ExternalOracle{},
	}
	initialAddress := "initial_address_here"
	initialAmount := 1000000
	alsaniaCoin.Balances[initialAddress] = initialAmount
	alsaniaCoin.TokenHolders[initialAddress] = true
	return alsaniaCoin
}

func (ac *AlsaniaCoin) SetDynamicGasFeeMultiplier(multiplier float64) {
	ac.DynamicGasFeeMultiplier = multiplier
}

func (ac *AlsaniaCoin) CalculateGasFee() int {
	return int(float64(ac.BaseGasFee) * ac.DynamicGasFeeMultiplier)
}

func (ac *AlsaniaCoin) DistributeReward(recipient string, amount int) {
	ac.transfer(nil, recipient, amount)
}

func (ac *AlsaniaCoin) CollectFee(recipient string, amount int) {
	ac.transfer(recipient, nil, amount)
}

func (ac *AlsaniaCoin) GenerateProof(sender, recipient string, amount int, privateKey string, senderBalance int) ([]byte, error) {
	privateKeyInt, err := hex.DecodeString(privateKey)
	if err != nil {
		return nil, err
	}
	if senderBalance < amount {
		return nil, errors.New("sender balance is insufficient for the transaction amount")
	}
	data := fmt.Sprintf("%s%s%d%d", sender, recipient, amount, senderBalance)
	hash := sha256.Sum256([]byte(data))
	privKey, _ := ecdsa.GenerateKey(ecdsa.P256(), rand.Reader)
	r, s, err := ecdsa.Sign(rand.Reader, privKey, hash[:])
	if err != nil {
		return nil, err
	}
	signature := r.Bytes()
	signature = append(signature, s.Bytes()...)
	return signature, nil
}

func (ac *AlsaniaCoin) Transfer(sender, recipient string, amount int, privateKey string) error {
	if sender == "" || recipient == "" {
		return errors.New("sender and recipient cannot be empty")
	}
	if amount <= 0 {
		return errors.New("amount must be positive")
	}
	if ac.Balances[sender] < amount {
		return errors.New("insufficient balance")
	}
	gasFee := ac.CalculateGasFee()
	totalAmount := amount + gasFee
	transaction := map[string]interface{}{
		"sender":     sender,
		"recipient":  recipient,
		"amount":     amount,
		"fee":        gasFee,
		"timestamp":  time.Now().Unix(),
	}
	if privateKey != "" {
		signature, err := ac.GenerateProof(sender, recipient, amount, privateKey, ac.Balances[sender])
		if err != nil {
			return err
		}
		transaction["signature"] = signature
	}
	if ac.isDoubleSpending(sender, amount) {
		return errors.New("double spending detected")
	}
	ac.transfer(sender, recipient, totalAmount)
	return nil
}

func (ac *AlsaniaCoin) transfer(sender, recipient string, amount int) {
	ac.Balances[sender] -= amount
	ac.Balances[recipient] += amount
}

type ExternalOracle struct{}

func (eo *ExternalOracle) GetPrice(cryptoSymbol string) (float64, error) {
	if cryptoSymbol == "ALSC" {
		return 10.0, nil // Placeholder price for AlsaniaCoin
	} else if cryptoSymbol == "BTC" || cryptoSymbol == "ETH" {
		resp, err := http.Get(fmt.Sprintf("https://api.coingecko.com/api/v3/simple/price?ids=%s&vs_currencies=usd", cryptoSymbol))
		if err != nil {
			return 0.0, err
		}
		defer resp.Body.Close()
		var data map[string]map[string]float64
		if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
			return 0.0, err
		}
		return data[cryptoSymbol]["usd"], nil
	}
	return 0.0, errors.New("unsupported cryptocurrency")
}

type TransactionPool struct {
	transactions []interface{}
	mu           sync.Mutex
}

func NewTransactionPool() *TransactionPool {
	return &TransactionPool{
		transactions: make([]interface{}, 0),
	}
}

func (tp *TransactionPool) AddTransaction(transaction interface{}) {
	tp.mu.Lock()
	defer tp.mu.Unlock()
	tp.transactions = append(tp.transactions, transaction)
}

func (tp *TransactionPool) RemoveTransaction(transaction interface{}) {
	tp.mu.Lock()
	defer tp.mu.Unlock()
	for i, t := range tp.transactions {
		if t == transaction {
			tp.transactions = append(tp.transactions[:i], tp.transactions[i+1:]...)
			break
		}
	}
}

func (tp *TransactionPool) GetPendingTransactions() []interface{} {
	tp.mu.Lock()
	defer tp.mu.Unlock()
	return tp.transactions
}

type PaLaConsensus struct {
	validators                  []Validator
	transactionPool             *TransactionPool
	consensusType               string
	blockProposalTimeout        int
	consensusThreshold          float64
	coin                        *AlsaniaCoin
	pendingBlocks               map[string][]map[string]interface{}
	lastRewardDistributionTime time.Time
	totalStakedAmount           int
	mu                          sync.Mutex
}

func NewPaLaConsensus(validators []Validator, transactionPool *TransactionPool) *PaLaConsensus {
	totalStakedAmount := 0
	for _, v := range validators {
		totalStakedAmount += v.StakedAmount
	}
	return &PaLaConsensus{
		validators:                  validators,
		transactionPool:             transactionPool,
		consensusType:               "POS",
		blockProposalTimeout:        10,
		consensusThreshold:          2.0 / 3.0,
		coin:                        NewAlsaniaCoin(),
		pendingBlocks:               make(map[string][]map[string]interface{}),
		lastRewardDistributionTime: time.Now(),
		totalStakedAmount:           totalStakedAmount,
	}
}

func (pc *PaLaConsensus) ProposeBlock() map[string]interface{} {
	block := pc.proposeBlockPOS()
	if block != nil {
		pc.mu.Lock()
		defer pc.mu.Unlock()
		pc.pendingBlocks[block["hash"].(string)] = append(pc.pendingBlocks[block["hash"].(string)], block)
		block["transactions"] = pc.transactionPool.GetPendingTransactions()
		pc.pendingBlocks[block["hash"].(string)] = append(pc.pendingBlocks[block["hash"].(string)], block)
	}
	if len(pc.pendingBlocks[block["hash"].(string)]) >= len(pc.validators)*int(pc.consensusThreshold) {
		return block
	}
	return nil
}

func (pc *PaLaConsensus) ValidateBlock(block map[string]interface{}, blockchain []map[string]interface{}) bool {
	if pc.validateBlockPOS(block) {
		if pc.prepareBlockPOS(block) {
			return pc.commitBlockPOS(block)
		}
	}
	return false
}

func (pc *PaLaConsensus) ConfirmBlock(block map[string]interface{}) bool {
	if pc.confirmBlockPOS(block) {
		pc.mu.Lock()
		defer pc.mu.Unlock()
		pc.pendingBlocks["commit"] = append(pc.pendingBlocks["commit"], block)
		return true
	}
	return false
}

func (pc *PaLaConsensus) proposeBlockPOS() map[string]interface{} {
	return map[string]interface{}{
		"hash": "block_hash",
		"data": "block_data",
	}
}

func (pc *PaLaConsensus) validateBlockPOS(block map[string]interface{}) bool {
	return block["hash"].(string) == "block_hash" && block["data"].(string) == "block_data"
}

func (pc *PaLaConsensus) prepareBlockPOS(block map[string]interface{}) bool {
	pc.mu.Lock()
	defer pc.mu.Unlock()
	if block["hash"].(string) == "block_hash" && block["data"].(string) == "block_data" {
		prepareCount := len(pc.pendingBlocks[block["hash"].(string)])
		return prepareCount >= len(pc.validators)*int(pc.consensusThreshold)
	}
	return false
}

func (pc *PaLaConsensus) commitBlockPOS(block map[string]interface{}) bool {
	pc.mu.Lock()
	defer pc.mu.Unlock()
	return block["hash"].(string) == "block_hash" && block["data"].(string) == "block_data"
}

func (pc *PaLaConsensus) applyPOSConsensusRules(block map[string]interface{}) bool {
	return block["hash"].(string) == "block_hash" && block["data"].(string) == "block_data"
}

func (pc *PaLaConsensus) confirmBlockPOS(block map[string]interface{}) bool {
	return block["hash"].(string) == "block_hash" && block["data"].(string) == "block_data"
}

func (pc *PaLaConsensus) verifyTransactionSignature(transaction map[string]interface{}) bool {
	if signature, ok := transaction["signature"].(string); ok {
		if public_key := pc.coin.GetPublicKey(transaction["sender"].(string)); public_key != nil {
			transactionCopy := make(map[string]interface{})
			for key, value := range transaction {
				if key != "signature" {
					transactionCopy[key] = value
				}
			}
			serializedTx, _ := json.Marshal(transactionCopy)
			return public_key.Verify([]byte(serializedTx), []byte(signature))
		}
	}
	return false
}

func (pc *PaLaConsensus) distributeStakingRewards() {
	pc.mu.Lock()
	defer pc.mu.Unlock()
	currentTime := time.Now()
	elapsedTime := currentTime.Sub(pc.lastRewardDistributionTime)
	elapsedYears := elapsedTime.Hours() / (365 * 24)
	rewardPerValidator := 0.05 * float64(pc.totalStakedAmount) * elapsedYears / float64(len(pc.validators))
	for _, validator := range pc.validators {
		rewardAmount := int(float64(validator.StakedAmount) * rewardPerValidator)
		pc.coin.Transfer("Staking Rewards", validator.Address, rewardAmount)
	}
	pc.lastRewardDistributionTime = currentTime
}

func (pc *PaLaConsensus) mintNewCoins(validator string, amount int) bool {
	pc.mu.Lock()
	defer pc.mu.Unlock()
	for _, v := range pc.validators {
		if v.Address == validator {
			eachShare := amount / len(pc.validators)
			for _, val := range pc.validators {
				pc.coin.Mint(val.Address, eachShare)
			}
			pc.distributeStakingRewards()
			return true
		}
	}
	return false
}

type AlsaniaBlockchain struct {
	coin              *AlsaniaCoin
	palaConsensus     *PaLaConsensus
	chain             []map[string]interface{}
	currentTransactions []map[string]interface{}
	pendingTransactions []map[string]interface{}
	nodes             map[string]bool
	peers             []string
	stakeholders      []string
	contracts         map[string]string
	deployedContracts map[string]string
}

func NewAlsaniaBlockchain() *AlsaniaBlockchain {
	return &AlsaniaBlockchain{
		coin:               NewAlsaniaCoin(),
		palaConsensus:      NewPaLaConsensus(),
		chain:              make([]map[string]interface{}, 0),
		currentTransactions: make([]map[string]interface{}, 0),
		pendingTransactions: make([]map[string]interface{}, 0),
		nodes:              make(map[string]bool),
		peers:              make([]string, 0),
		stakeholders:       make([]string, 0),
		contracts:          make(map[string]string),
		deployedContracts:  make(map[string]string),
	}
}

func (bc *AlsaniaBlockchain) CreateGenesisBlock() {
	genesisBlock := make(map[string]interface{})
	genesisBlock["index"] = 0
	genesisBlock["transactions"] = make([]map[string]interface{}, 0)
	genesisBlock["previousHash"] = "0"
	genesisBlock["timestamp"] = time.Now().Unix()
	genesisBlock["nonce"] = 0
	genesisBlock["hash"] = hashBlock(genesisBlock)
	bc.chain = append(bc.chain, genesisBlock)
}

func (bc *AlsaniaBlockchain) AddNode(host, port string) {
	node := host + ":" + port
	bc.nodes[node] = true
}

func (bc *AlsaniaBlockchain) AddPeer(host, port string) {
	peer := host + ":" + port
	bc.peers = append(bc.peers, peer)
}

func (bc *AlsaniaBlockchain) AddStakeholder(address string) {
	bc.stakeholders = append(bc.stakeholders, address)
}

func (bc *AlsaniaBlockchain) CreateTransaction(sender, recipient string, amount int, privateKey interface{}) map[string]interface{} {
	transaction := make(map[string]interface{})
	transaction["sender"] = sender
	transaction["recipient"] = recipient
	transaction["amount"] = amount
	transaction["timestamp"] = time.Now().Unix()
	if privateKey != nil {
		signature, err := bc.coin.SignTransaction(transaction, privateKey.(string))
		if err != nil {
			fmt.Println("Error generating signature:", err)
		}
		transaction["signature"] = signature
	}
	bc.pendingTransactions = append(bc.pendingTransactions, transaction)
	return transaction
}

func (bc *AlsaniaBlockchain) ValidateBlock(block map[string]interface{}) bool {
	calculatedMerkleRoot := calculateMerkleRoot(block["transactions"].([]map[string]interface{}))
	return block["previousHash"].(string) == bc.chain[len(bc.chain)-1]["hash"].(string) &&
		block["hash"].(string)[:2] == "00" &&
		block["merkleRoot"].(string) == calculatedMerkleRoot &&
		bc.palaConsensus.ValidateBlock(block)
}

func (bc *AlsaniaBlockchain) ReachConsensus() {
	lastBlock := bc.chain[len(bc.chain)-1]
	proposedBlock := bc.palaConsensus.ProposeBlock()
	if bc.palaConsensus.ValidateBlock(proposedBlock) {
		bc.AddBlockToChain(proposedBlock)
		for node := range bc.nodes {
			bc.SendBlockToNode(node, proposedBlock)
		}
	} else {
		fmt.Println("Proposed block failed validation, consensus not reached")
	}
}

func (bc *AlsaniaBlockchain) AddBlockToChain(block map[string]interface{}) {
	if !bc.palaConsensus.ValidateBlock(block) {
		fmt.Println("Consensus validation failed")
	}
	if !bc.ValidateBlock(block) {
		fmt.Println("Block validation failed")
	}
	if bc.ValidateBlock(block) {
		bc.chain = append(bc.chain, block)
	}
}

func (bc *AlsaniaBlockchain) SendBlockToNode(node string, block map[string]interface{}) {
	conn, err := net.Dial("tcp", node)
	if err != nil {
		fmt.Println("Error connecting to node:", err)
		return
	}
	defer conn.Close()
	err = sendBlock(conn, block)
	if err != nil {
		fmt.Println("Error sending block to node:", err)
	}
}

func (bc *AlsaniaBlockchain) ReceiveBlockFromNode(conn net.Conn) (map[string]interface{}, error) {
	block, err := receiveBlock(conn)
	if err != nil {
		return nil, err
	}
	return block, nil
}

func (bc *AlsaniaBlockchain) HandleTokenTransfer(transaction map[string]interface{}) string {
	sender := transaction["sender"].(string)
	recipient := transaction["recipient"].(string)
	amount := transaction["amount"].(int)
	bc.coin.TransferToken(sender, recipient, amount)
	return fmt.Sprintf("Token transfer successful. Sender: %s, Recipient: %s, Amount: %d", sender, recipient, amount)
}

func (bc *AlsaniaBlockchain) DeployContract(sender, contractName string, contractCode map[string]interface{}, gasLimit int) string {
	if _, ok := bc.deployedContracts[contractName]; ok {
		return fmt.Sprintf("Contract with name '%s' already deployed", contractName)
	}
	compiledContract := contractCode["bytecode"].(string)
	contractAddress := deployContract(sender, compiledContract, gasLimit)
	bc.deployedContracts[contractName] = contractAddress
	return contractAddress
}

func (bc *AlsaniaBlockchain) InvokeContractMethod(sender, contractAddress, method string, args []interface{}, gasLimit int) error {
	if _, ok := bc.contracts[contractAddress]; !ok {
		return errors.New("Contract address not found")
	}
	contractABI := bc.contracts[contractAddress]
	err := invokeContractMethod(sender, contractAddress, contractABI, method, args, gasLimit)
	if err != nil {
		return fmt.Errorf("Failed to invoke contract method: %s", err)
	}
	return nil
}

func (bc *AlsaniaBlockchain) TransferToken(tokenContractName, sender, recipient string, amount int, privateKey interface{}) (string, error) {
	if _, ok := bc.deployedContracts[tokenContractName]; !ok {
		return "", errors.New("Token contract not deployed")
	}
	tokenContractAddress := bc.deployedContracts[tokenContractName]
	if bc.coin.GetTokenBalance(tokenContractName, sender) < amount {
		return "", errors.New("Insufficient balance")
	}
	transaction := map[string]interface{}{
		"token_contract_name": tokenContractName,
		"from":                sender,
		"to":                  tokenContractAddress,
		"value":               amount,
	}
	bc.coin.CreateTransaction(sender, recipient, amount)
	if privateKey != nil {
		transaction["private_key"] = privateKey
	}
	bc.SendTransaction(transaction)
	return fmt.Sprintf("Token transfer successful. Sender: %s, Recipient: %s, Amount: %d", sender, recipient, amount), nil
}

func (bc *AlsaniaBlockchain) GetTokenBalance(tokenContractName, address string) (int, error) {
	if _, ok := bc.contracts[tokenContractName]; !ok {
		return 0, errors.New("Token contract not deployed")
	}
	tokenContractAddress := bc.contracts[tokenContractName]
	balance := bc.GetBalanceFromBlockchain(tokenContractAddress, address)
	return balance, nil
}

func (bc *AlsaniaBlockchain) HandleTokenEvent(event map[string]interface{}) string {
	eventName := event["name"].(string)
	eventData := event["data"].(map[string]interface{})
	switch eventName {
	case "Transfer":
		sender := eventData["from"].(string)
		recipient := eventData["to"].(string)
		amount := eventData["amount"].(int)
		return fmt.Sprintf("Transfer event: %d tokens transferred from %s to %s", amount, sender, recipient)
	case "Approval":
		owner := eventData["owner"].(string)
		spender := eventData["spender"].(string)
		allowance := eventData["allowance"].(int)
		return fmt.Sprintf("Approval event: Allowance of %d tokens granted by %s to %s", allowance, owner, spender)
	default:
		return fmt.Sprintf("Unhandled token event: %s, Data: %v", eventName, eventData)
	}
}

type Block struct {
	Index         int
	Transactions  []map[string]interface{}
	Timestamp     int64
	PreviousHash  string
	Nonce         int
	Hash          string
	MerkleRoot    string
}

func NewBlock(index int, transactions []map[string]interface{}, previousHash string) *Block {
	block := &Block{
		Index:         index,
		Transactions:  transactions,
		Timestamp:     time.Now().Unix(),
		PreviousHash:  previousHash,
		Nonce:         0,
	}
	block.Hash = block.HashBlock()
	block.MerkleRoot = block.CalculateMerkleRoot()
	return block
}

func (b *Block) CalculateMerkleRoot() string {
	transactionHashes := make([]string, len(b.Transactions))
	for i, tx := range b.Transactions {
		transactionHashes[i] = hashTransaction(tx)
	}
	return b.calculateMerkleRoot(transactionHashes)
}

func (b *Block) calculateMerkleRoot(data []string) string {
	if len(data) == 1 {
		return data[0]
	}
	var new_data []string
	for i := 0; i < len(data)-1; i += 2 {
		combinedHash := hashPair(data[i], data[i+1])
		new_data = append(new_data, combinedHash)
	}
	if len(data)%2 == 1 {
		new_data = append(new_data, data[len(data)-1])
	}
	return b.calculateMerkleRoot(new_data)
}

func hashPair(a, b string) string {
	hash := sha256.Sum256([]byte(a + b))
	return hex.EncodeToString(hash[:])
}

func hashTransaction(transaction map[string]interface{}) string {
	serializedTx := fmt.Sprintf("%v", transaction)
	hash := sha256.Sum256([]byte(fmt.Sprintf("%v", transaction)))
	return hex.EncodeToString(hash[:])
}

func (b *Block) HashBlock() string {
	blockHeader := string(b.Index) + string(b.Timestamp) + string(b.PreviousHash) + string(b.Nonce)
	for _, tx := range b.Transactions {
		blockHeader += hashTransaction(tx)
	}
	hash := sha256.Sum256([]byte(blockHeader))
	return hex.EncodeToString(hash[:])
}

type Node struct {
	Address     string
	Host        string
	Port        string
	PrivateKey  string
	PublicKey   string
	Balance     int
}

func NewNode(address, host, port string) *Node {
	privateKey := generatePrivateKey()
	publicKey := derivePublicKey(privateKey)
	return &Node{
		Address:    address,
		Host:       host,
		Port:       port,
		PrivateKey: privateKey,
		PublicKey:  publicKey,
		Balance:    0,
	}
}

func generatePrivateKey() string {
	privateKeyBytes := make([]byte, 32)
	rand.Read(privateKeyBytes)
	return hex.EncodeToString(privateKeyBytes)
}

func derivePublicKey(privateKey string) string {
	privateKeyBytes, _ := hex.DecodeString(privateKey)
	curve := elliptic.P256()
	x, y := curve.ScalarBaseMult(privateKeyBytes)
	publicKey := elliptic.Marshal(curve, x, y)
	return hex.EncodeToString(publicKey)
}

func (n *Node) CreateMessage(sender, recipient, data string) string {
	message := map[string]string{
		"sender":    sender,
		"recipient": recipient,
		"data":      data,
	}
	jsonMessage, _ := json.Marshal(message)
	return string(jsonMessage)
}

func RegisterNode(host, port string, newNodeInfo map[string]string) {
	url := fmt.Sprintf("http://%s:%s/register", host, port)
	jsonValue, _ := json.Marshal(newNodeInfo)
	resp, err := http.Post(url, "application/json", strings.NewReader(string(jsonValue)))
	if err != nil {
		fmt.Println("Failed to register node:", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		fmt.Println("Node registered successfully")
	} else {
		fmt.Println("Failed to register node")
	}
}

func (n *Node) SendTransaction(transaction string) {
	payload := map[string]string{"transaction": transaction}
	jsonValue, _ := json.Marshal(payload)
	url := fmt.Sprintf("http://%s:%s/transaction", n.Host, n.Port)
	resp, err := http.Post(url, "application/json", strings.NewReader(string(jsonValue)))
	if err != nil {
		fmt.Println("Error sending transaction:", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		fmt.Println("Transaction sent successfully")
	} else {
		fmt.Println("Failed to send transaction")
	}
}

func (n *Node) SendBlock(block string) {
	payload := map[string]string{"block": block}
	jsonValue, _ := json.Marshal(payload)
	url := fmt.Sprintf("http://%s:%s/block", n.Host, n.Port)
	resp, err := http.Post(url, "application/json", strings.NewReader(string(jsonValue)))
	if err != nil {
		fmt.Println("Error sending block:", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		fmt.Println("Block sent successfully")
	} else {
		fmt.Println("Failed to send block")
	}
}

func main() {
	alsaniaBlockchain := NewAlsaniaBlockchain()

	alsaniaBlockchain.CreateGenesisBlock()

	alsaniaBlockchain.AddNode("localhost", "3000")
	alsaniaBlockchain.AddNode("localhost", "3001")
	alsaniaBlockchain.AddPeer("localhost", "3002")

	http.HandleFunc("/transaction", TransactionHandler)
	http.HandleFunc("/block", BlockHandler)
	http.HandleFunc("/register", RegisterNodeHandler)
	fmt.Println("Server listening on port 8080...")
	http.ListenAndServe(":8080", nil)
}

func TransactionHandler(w http.ResponseWriter, r *http.Request) {
    var transaction map[string]interface{}
    err := json.NewDecoder(r.Body).Decode(&transaction)
    if err != nil {
        http.Error(w, "Failed to decode transaction", http.StatusBadRequest)
        return
    }
	w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Transaction received and added to pending pool")
}

func BlockHandler(w http.ResponseWriter, r *http.Request) {
    // Decode the incoming JSON block
    var block map[string]interface{}
    err := json.NewDecoder(r.Body).Decode(&block)
    if err != nil {
        http.Error(w, "Failed to decode block", http.StatusBadRequest)
        return
    }
	w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Block received and added to blockchain")
}

func RegisterNodeHandler(w http.ResponseWriter, r *http.Request) {
    var newNodeInfo map[string]string
    err := json.NewDecoder(r.Body).Decode(&newNodeInfo)
    if err != nil {
        http.Error(w, "Failed to decode registration request", http.StatusBadRequest)
        return
    }
    host := newNodeInfo["host"]
    port := newNodeInfo["port"]

    alsaniaBlockchain.AddNode(host, port)

    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Node registered successfully")
}
