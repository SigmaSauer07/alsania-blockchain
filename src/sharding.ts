import { Blockchain } from './blockchain';

export class Sharding {
    private blockchain: Blockchain;
    private shards: Map<number, Blockchain>;

    constructor(blockchain: Blockchain) {
        this.blockchain = blockchain;
        this.shards = new Map();
    }

    createShard(shardId: number) {
        const shardBlockchain = new Blockchain();
        this.shards.set(shardId, shardBlockchain);
    }

    getShard(shardId: number): Blockchain | undefined {
        return this.shards.get(shardId);
    }

    async addBlockToShard(shardId: number, data: any) {
        const shard = this.shards.get(shardId);
        if (shard) {
            await shard.addBlock(data);
        }
    }

    validateShards() {
        for (const shard of this.shards.values()) {
            shard.validateChain();
        }
    }
}
