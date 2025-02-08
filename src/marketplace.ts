import { ethers } from 'ethers';

export class Marketplace {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private marketplaceContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, marketplaceContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.marketplaceContractAddress = marketplaceContractAddress;
    }

    async listItem(item: any) {
        const marketplaceContract = new ethers.Contract(this.marketplaceContractAddress, /* ABI array */, this.signer);
        const tx = await marketplaceContract.listItem(item);
        await tx.wait();
        return tx;
    }

    async buyItem(itemId: number) {
        const marketplaceContract = new ethers.Contract(this.marketplaceContractAddress, /* ABI array */, this.signer);
        const tx = await marketplaceContract.buyItem(itemId);
        await tx.wait();
        return tx;
    }

    async getItem(itemId: number) {
        const marketplaceContract = new ethers.Contract(this.marketplaceContractAddress, /* ABI array */, this.signer);
        const item = await marketplaceContract.getItem(itemId);
        return item;
    }
}
