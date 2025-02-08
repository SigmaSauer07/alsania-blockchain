import { ethers } from 'ethers';

export class IdentityVerification {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private identityVerificationContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, identityVerificationContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.identityVerificationContractAddress = identityVerificationContractAddress;
    }

    async verifyIdentity(identityProof: any) {
        const identityVerificationContract = new ethers.Contract(this.identityVerificationContractAddress, /* ABI array */, this.signer);
        const tx = await identityVerificationContract.verifyIdentity(identityProof);
        await tx.wait();
        return tx;
    }

    async getVerificationStatus(userAddress: string) {
        const identityVerificationContract = new ethers.Contract(this.identityVerificationContractAddress, /* ABI array */, this.signer);
        const status = await identityVerificationContract.getVerificationStatus(userAddress);
        return status;
    }
}
