import { ethers } from 'ethers';

export class Oracle {
    private provider: ethers.providers.JsonRpcProvider;
    private signer: ethers.Signer;
    private oracleContractAddress: string;

    constructor(rpcUrl: string, privateKey: string, oracleContractAddress: string) {
        this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
        this.signer = new ethers.Wallet(privateKey, this.provider);
        this.oracleContractAddress = oracleContractAddress;
    }

    async requestData(dataType: string) {
        const oracleContract = new ethers.Contract(this.oracleContractAddress, /* ABI array */, this.signer);
        const tx = await oracleContract.requestData(dataType);
        await tx.wait();
        return tx;
    }

    async getData(dataType: string) {
        const oracleContract = new ethers.Contract(this.oracleContractAddress, /* ABI array */, this.signer);
        const data = await oracleContract.getData(dataType);
        return data;
    }
}
