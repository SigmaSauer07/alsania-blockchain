import { SmartContract } from './smartContract';

export class Governance {
    private smartContract: SmartContract;
    private governanceContractAddress: string;

    constructor(smartContract: SmartContract, governanceContractAddress: string) {
        this.smartContract = smartContract;
        this.governanceContractAddress = governanceContractAddress;
    }

    async proposeChange(abi: any, method: string, ...args: any[]) {
        return await this.smartContract.interactWithContract(this.governanceContractAddress, abi, method, ...args);
    }

    async voteOnProposal(abi: any, method: string, proposalId: number, vote: boolean) {
        return await this.smartContract.interactWithContract(this.governanceContractAddress, abi, method, proposalId, vote);
    }

    async getProposal(abi: any, method: string, proposalId: number) {
        return await this.smartContract.interactWithContract(this.governanceContractAddress, abi, method, proposalId);
    }
}
