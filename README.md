# Storage Proofs
Curve DAO — along with core projects like crvUSD — lives on Ethereum.
New deployments depend on governance and data stored on Ethereum.

The simplest and most robust way to support multiple transport layers is to send **blockhashes** or **state roots** from Ethereum, and use **storage proofs** on other chains.
This abstracts away the messaging protocol — dApps just verify data against the known Ethereum root.

![approach](docs/blockhash_approach.png)

You can find LZ Blockhash Oracle infra at [curvefi/blockhash-oracle](https://github.com/curvefi/blockhash-oracle).

## Storage proof
Each block has a **block header**, which includes the **state root** — a root hash of the entire Merkle Patricia Trie containing accounts and storage.
Given a blockhash, you can verify the state root.
On this graph, you see a trie with its root at the top, branching into nested nodes.

![storage proof](docs/storage_proof.png)

To prove a storage slot, you must verify the full path from the root down to the leaf node — or prove that it doesn’t exist.
In red, you can see the exact proof path.

## System Specification

### Overview

The system relies on the following actors:
- An offchain prover (from now on the prover), whose role is to fetch data from Ethereum that are useful to compute the growth rate of the vault, alongside with a proof that those data are valid.
- A smart contract that will be called by the prover (from now on the verifier) that will verify that the data provided alongside their proof.
- A smart contract that will provide the current price of scrvUSD, given the growth rate of the vault provided by the prover and verified by the verifier, to be used by the stableswap-ng pool on the target chain.

Depending on the type of chain the proof (and hence its verification process) will be different:
- On OP Stack-based chains the verifier will expect a blockhash (to be matched with the one available in a precompile) and a state proof of the memory slots relevant to the growth rate computation.
- On Taiko Stack-based chains the verifier will expect the blocknumber and a state proof of the memory slots relevant to the growth rate computation.
- On all other chains the prover will provide the same data as for the OP Stack, and relevant data to verify the proof will be bridged from Optimism using L0.

Here's the flowchart of the system for an OP Stack-based chain:
```mermaid
flowchart TD
    A[Prover] --> |Generates from L1 state| E[State Proof]
    E[State Proof] --> B[Verifier Contract]
    B -->|Push update price if proof is correct| C[Price Oracle Contract]
    C -->|Provides scrvUSD price| D[stableswap-ng Pool]

    subgraph L2 Chain
        E2[Precompile] --> |Used to obtain| E1
        E1[L1 Blockhash] --> B
    end
```

### Prover's trust assumptions
#### Safety
The prover doesn't need to be trusted as the safety of the whole system relies on the fact that it is not feasible to push an update with a forged proof.
#### Liveness
The prover needs to be online to provide the proof in a timely manner, if the prover is offline the system might not be able to provide a correct (or accurate) price for scrvUSD.

## Contributing

### Install
Install python dependencies using [uv](https://github.com/astral-sh/uv):

```shell
uv sync
```

To enter the python environment:

```shell
source .venv/bin/activate
```

Solidity dependencies:
    
```shell
solc-select install 0.8.18
solc-select use 0.8.18

npm install solidity-rlp@2.0.7
```

Completely sync submodules and remove all unnecessary files:
```shell
git submodule update --init --recursive --depth 1
find contracts/xdao -mindepth 1 -maxdepth 1 ! -name 'contracts' -exec rm -rf {} +
find tests/scrvusd/contracts/scrvusd -depth -mindepth 1 ! -wholename 'tests/scrvusd/contracts/scrvusd/contracts/yearn/VaultV3.vy' -type f -delete
find tests/scrvusd/contracts/scrvusd -depth -type d -empty -delete
find tests/xgov/contracts/curve-xgov -mindepth 1 -maxdepth 1 ! -name 'contracts' -exec rm -rf {} +
```

### Test
```shell
uv run pytest .
```
Forked and slow stateful tests are disabled by default. To include them, use the --forked or --slow flags. For example, to run all tests:
```shell
uv run pytest --forked --slow
```

### Run
You can find keeper scripts in [scripts/](scripts) directory. Blockhash Oracles support TBD.

## Acknowledgements
This works builds on top of the work done by the Lido team when building [their oracle](https://github.com/lidofinance/curve-merkle-oracle/blob/fffd375659358af54a6e8bbf8c3aa44188894c81/contracts/StableSwapStateOracle.sol#L295) for wstETH pools on stableswap-ng.

# Usages
## scrvUSD Price Oracle
### Why is this needed?
At Curve, we offer a Savings Vault for crvUSD, an ERC4626 token that allows to earn
a "risk-free" interest rate on the crvUSD stablecoin.

When bridging scrvUSD crosschain, the token loses its ERC4626 capabilities and becomes
a plain ERC20 token that can not be minted with nor redeemed using crvUSD.

To ease this problem we opted to have secondary scrvUSD markets on all chains where scrvUSD can be redeemed. 
Since the price of the asset is not stable, we cannot use a "simple" [stableswap-ng](https://github.com/curvefi/stableswap-ng/blob/fd54b9a1a110d0e2e4f962583761d9e236b70967/contracts/main/CurveStableSwapNG.vy#L17) pool as the price
of the asset would go up as the yield accrues. Fortunately stableswap-ng supports "oraclized" assets,
which means that we can use an oracle to provide the rate at which the price of the asset is increasing
and the pool will work as expected.

### Problem
It is a hard problem to guarantee the correctness of the value provided by the oracle, if not precise enough this can
lead to MEV in the liquidity pool, at a loss for the liquidity providers. Even worse if someone is able to manipulate
this rate it can lead to the pool being drained from one side.

### Solution

This repository contains [a solution](contracts/scrvusd) that fetches data from Ethereum, where scrvUSD lives and provides them on other
chains, with the goal of being able to compute the growth rate in a safe (non-manipulable) and precise 
(no losses due to approximation) way. Furthermore, this oracle can allow to create stableswap-ng pools for other assets
like USDC/scrvUSD, FRAX/scrvUSD, etc.

# Sources
- [Presentation](docs/Cross-chain%20Public%20Goods.pdf)
