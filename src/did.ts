import { ethers } from 'ethers';

export class DID {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private didContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, didContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.didContractAddress = didContractAddress;
    }

    async createDID(didDocument: any) {
        const didContract = new ethers.Contract(this.didContractAddress, /* ABI array */, this.signer);
        const tx = await didContract.createDID(didDocument);
        await tx.wait();
        return tx;
    }

    async updateDID(did: string, didDocument: any) {
        const didContract = new ethers.Contract(this.didContractAddress, /* ABI array */, this.signer);
        const tx = await didContract.updateDID(did, didDocument);
        await tx.wait();
        return tx;
    }

    async getDID(did: string) {
        const didContract = new ethers.Contract(this.didContractAddress, /* ABI array */, this.signer);
        const didDocument = await didContract.getDID(did);
        return didDocument;
    }
}
