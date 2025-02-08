import { ethers } from 'ethers';

export class Voting {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private votingContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, votingContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.votingContractAddress = votingContractAddress;
    }

    async createProposal(proposal: any) {
        const votingContract = new ethers.Contract(this.votingContractAddress, /* ABI array */, this.signer);
        const tx = await votingContract.createProposal(proposal);
        await tx.wait();
        return tx;
    }

    async voteOnProposal(proposalId: number, vote: boolean) {
        const votingContract = new ethers.Contract(this.votingContractAddress, /* ABI array */, this.signer);
        const tx = await votingContract.voteOnProposal(proposalId, vote);
        await tx.wait();
        return tx;
    }

    async getProposal(proposalId: number) {
        const votingContract = new ethers.Contract(this.votingContractAddress, /* ABI array */, this.signer);
        const proposal = await votingContract.getProposal(proposalId);
        return proposal;
    }
}
