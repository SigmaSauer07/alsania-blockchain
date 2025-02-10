import React, { useState } from 'react';
import Web3 from 'web3';
import { create } from 'ipfs-http-client';
import { abi } from './contractAbi';
import { contractAddress } from './contractAddress';

const App = () => {
  const [account, setAccount] = useState('');
  const [ipfsHash, setIpfsHash] = useState('');
  const [stakeAmount, setStakeAmount] = useState('');
  const [proposalId, setProposalId] = useState('');
  const [support, setSupport] = useState(false);
  const [embers, setEmbers] = useState('');
  const [alsc, setAlsc] = useState('');

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
    const contract = new web3.eth.Contract(abi, contractAddress);
    await contract.methods.stake(amount).send({ from: account });
  };

  const voteOnProposal = async (proposalId, support) => {
    const contract = new web3.eth.Contract(abi, contractAddress);
    await contract.methods.vote(proposalId, support).send({ from: account });
  };

  const convertToEmbers = async (amount) => {
    const contract = new web3.eth.Contract(abi, contractAddress);
    const embers = await contract.methods.convertToEmbers(amount).call();
    setEmbers(embers);
  };

  const convertFromEmbers = async (embers) => {
    const contract = new web3.eth.Contract(abi, contractAddress);
    const alsc = await contract.methods.convertFromEmbers(embers).call();
    setAlsc(alsc);
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
      <input
        type="number"
        value={proposalId}
        onChange={(e) => setProposalId(e.target.value)}
        placeholder="Proposal ID"
      />
      <label>
        Support:
        <input
          type="checkbox"
          checked={support}
          onChange={(e) => setSupport(e.target.checked)}
        />
      </label>
      <button onClick={() => voteOnProposal(proposalId, support)}>Vote</button>
      <input
        type="number"
        value={alsc}
        onChange={(e) => setAlsc(e.target.value)}
        placeholder="ALSC Amount"
      />
      <button onClick={() => convertToEmbers(alsc)}>Convert to Embers</button>
      <p>Embers: {embers}</p>
      <input
        type="number"
        value={embers}
        onChange={(e) => setEmbers(e.target.value)}
        placeholder="Embers Amount"
      />
      <button onClick={() => convertFromEmbers(embers)}>Convert to ALSC</button>
      <p>ALSC: {alsc}</p>
    </div>
  );
};

export default App;
