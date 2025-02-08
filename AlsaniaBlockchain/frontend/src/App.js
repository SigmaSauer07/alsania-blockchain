import React, { useState } from 'react';
import Web3 from 'web3';
import { create } from 'ipfs-http-client';

const App = () => {
  const [account, setAccount] = useState('');
  const [ipfsHash, setIpfsHash] = useState('');
  const [stakeAmount, setStakeAmount] = useState('');

  const web3 = new Web3(Web3.givenProvider || 'ws://localhost:9944');
  const ipfs = create('https://ipfs.infura.io:5001');

  const connectWallet = async () => {
    const accounts = await web3.eth.requestAccounts();
    setAccount(accounts[0]);
  };

  const uploadToIpfs = async (file) => {
    const result = await ipfs.add(file);
    setIpfsHash(result.path);
  };

  const stakeALSC = async (amount) => {
    const contractAddress = 'YOUR_CONTRACT_ADDRESS';
    const abi = [/* YOUR_CONTRACT_ABI */];
    const contract = new web3.eth.Contract(abi, contractAddress);
    await contract.methods.stake(amount).send({ from: account });
  };

  return (
    <div>
      <h1>Alsania Blockchain</h1>
      <button onClick={connectWallet}>Connect Wallet</button>
      <p>Account: {account}</p>
      <input type="file" onChange={(e) => uploadToIpfs(e.target.files[0])} />
      <p>IPFS Hash: {ipfsHash}</p>
      <input
        type="number"
        value={stakeAmount}
        onChange={(e) => setStakeAmount(e.target.value)}
        placeholder="Stake Amount"
      />
      <button onClick={() => stakeALSC(stakeAmount)}>Stake ALSC</button>
    </div>
  );
};

export default App;
