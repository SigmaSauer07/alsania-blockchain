import { ethers } from 'ethers';

export class Insurance {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private insuranceContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, insuranceContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.insuranceContractAddress = insuranceContractAddress;
    }

    async createPolicy(policy: any) {
        const insuranceContract = new ethers.Contract(this.insuranceContractAddress, /* ABI array */, this.signer);
        const tx = await insuranceContract.createPolicy(policy);
        await tx.wait();
        return tx;
    }

    async claimPolicy(policyId: number) {
        const insuranceContract = new ethers.Contract(this.insuranceContractAddress, /* ABI array */, this.signer);
        const tx = await insuranceContract.claimPolicy(policyId);
        await tx.wait();
        return tx;
    }

    async getPolicy(policyId: number) {
        const insuranceContract = new ethers.Contract(this.insuranceContractAddress, /* ABI array */, this.signer);
        const policy = await insuranceContract.getPolicy(policyId);
        return policy;
    }
}
