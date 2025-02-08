import { ethers } from 'ethers';

export class SmartContract {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;

    constructor(rpcUrl: string, privateKey: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
    }

    async deployContract(abi: any, bytecode: string, ...args: any[]) {
        const factory = new ethers.ContractFactory(abi, bytecode, this.signer);
        const contract = await factory.deploy(...args);
        await contract.deployed();
        return contract.address;
    }

    async interactWithContract(contractAddress: string, abi: any, method: string, ...args: any[]) {
        const contract = new ethers.Contract(contractAddress, abi, this.signer);
        const tx = await contract[method](...args);
        await tx.wait();
        return tx;
    }
}
