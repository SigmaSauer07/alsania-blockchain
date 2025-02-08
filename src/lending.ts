import { ethers } from 'ethers';

export class Lending {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private lendingContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, lendingContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.lendingContractAddress = lendingContractAddress;
    }

    async depositCollateral(collateral: any) {
        const lendingContract = new ethers.Contract(this.lendingContractAddress, /* ABI array */, this.signer);
        const tx = await lendingContract.depositCollateral(collateral);
        await tx.wait();
        return tx;
    }

    async borrowFunds(amount: number) {
        const lendingContract = new ethers.Contract(this.lendingContractAddress, /* ABI array */, this.signer);
        const tx = await lendingContract.borrowFunds(amount);
        await tx.wait();
        return tx;
    }

    async repayLoan(loanId: number) {
        const lendingContract = new ethers.Contract(this.lendingContractAddress, /* ABI array */, this.signer);
        const tx = await lendingContract.repayLoan(loanId);
        await tx.wait();
        return tx;
    }

    async getLoan(loanId: number) {
        const lendingContract = new ethers.Contract(this.lendingContractAddress, /* ABI array */, this.signer);
        const loan = await lendingContract.getLoan(loanId);
        return loan;
    }
}
