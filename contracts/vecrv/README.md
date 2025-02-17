## About
Gauges allow users to [boost rewards](https://resources.curve.fi/reward-gauges/boosting-your-crv-rewards/) using veCRV.
This project extends the same mechanism to other networks, enabling cross-chain functionality for veCRV.

## UX
### Update balance
Users must first update their balance on the desired Layer-2 (L2) network.
This is achieved by providing an Ethereum State Proof based on the available block hash or state root.
Detailed instructions for this process are available in the [`scripts`](../../scripts/vecrv) directory.
Since the nature of blockhash feeds varies across networks, regular updates are essential to maintain accurate data.
The architecture ensures these updates occur automatically, with a maximum frequency of once per week,
reducing manual effort.

### Delegate veCRV
Certain Ethereum addresses may not be accessible from other networks (e.g., [yCRV](https://etherscan.io/address/0x52f541764E6e90eeBc5c21Ff570De0e2D63766B6)).
To work around this limitation, you can delegate your veCRV balance to a new address.

#### **Delegation Steps**
1. Call `.allow_delegation(CHAIN_ID)` from your target contract to enable delegation for the desired chain.
2. From the address holding veCRV, call `.delegate(CHAIN_ID, target)` to delegate your balance to the target address.
3. Verify the delegation on the destination chain (one whose `CHAIN_ID` you used above) with the provided [script](../../scripts/vecrv).

#### **Important Notes**
- Delegations are managed via the **VecrvDelegate Contract** ([`VecrvDelegate.vy`](VecrvDelegate.vy)) on Ethereum mainnet, which acts as a centralized entity for delegations.
- Delegations are **one-to-one mappings**; positions cannot be merged across multiple addresses.
- If calls cannot be made from specific addresses, it is possible to initiate a DAO vote to configure delegation.

### Gauges
Here are a few technical details to consider:
- Certain gauges may require a `.update_voting_escrow()` call to retrieve the latest contract information.
- Your working balance is influenced by the gauge’s total supply. To ensure optimal rewards, it is recommended to call `.user_checkpoint(addr)` after new deposits.
