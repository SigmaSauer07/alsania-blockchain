import { ethers } from 'ethers';

export class DEX {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private dexContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, dexContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.dexContractAddress = dexContractAddress;
    }

    async addLiquidity(tokenA: string, tokenB: string, amountA: number, amountB: number) {
        const dexContract = new ethers.Contract(this.dexContractAddress, /* ABI array */, this.signer);
        const tx = await dexContract.addLiquidity(tokenA, tokenB, amountA, amountB);
        await tx.wait();
        return tx;
    }

    async removeLiquidity(tokenA: string, tokenB: string, liquidity: number) {
        const dexContract = new ethers.Contract(this.dexContractAddress, /* ABI array */, this.signer);
        const tx = await dexContract.removeLiquidity(tokenA, tokenB, liquidity);
        await tx.wait();
        return tx;
    }

    async swapTokens(tokenA: string, tokenB: string, amountA: number, amountBMin: number) {
        const dexContract = new ethers.Contract(this.dexContractAddress, /* ABI array */, this.signer);
        const tx = await dexContract.swapTokens(tokenA, tokenB, amountA, amountBMin);
        await tx.wait();
        return tx;
    }
}
