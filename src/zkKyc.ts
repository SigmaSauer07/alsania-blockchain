import { ethers } from 'ethers';

export class ZKKYC {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private kycContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, kycContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.kycContractAddress = kycContractAddress;
    }

    async verifyIdentity(identityProof: any) {
        const kycContract = new ethers.Contract(this.kycContractAddress, /* ABI array */, this.signer);
        const tx = await kycContract.verifyIdentity(identityProof);
        await tx.wait();
        return tx;
    }

    async getVerificationStatus(userAddress: string) {
        const kycContract = new ethers.Contract(this.kycContractAddress, /* ABI array */, this.signer);
        const status = await kycContract.getVerificationStatus(userAddress);
        return status;
    }
}
