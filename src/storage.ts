import { create } from 'ipfs-http-client';

export class Storage {
    private ipfs: any;

    constructor() {
        this.ipfs = create({ url: 'https://ipfs.infura.io:5001/api/v0' });
    }

    async addData(data: any) {
        const result = await this.ipfs.add(data);
        return result.path;
    }

    async getData(hash: string) {
        const stream = this.ipfs.cat(hash);
        let data = '';

        for await (const chunk of stream) {
            data += chunk.toString();
        }

        return data;
    }
}
