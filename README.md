# Protocol Name 

### Prize Pool TO BE FILLED OUT BY CYFRIN

- Total Pool - 
- H/M -  
- Low - 

- Starts: 
- Ends: 

- nSLOC: 

[//]: # (contest-details-open)

## About the Project

### Context
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

This project contains a solution that fetches data from Ethereum, where scrvUSD lives and provides them on other
chains, with the goal of being able to compute the growth rate in a safe (non-manipulable) and precise 
(no losses due to approximation) way. Furthermore, this oracle can allow to create stableswap-ng pools for other assets
like USDC/scrvUSD, FRAX/scrvUSD, etc.

### Implementation details

Since actual scrvUSD price is subject to changes on Ethereum,
it's impossible to predict price with 100% certainty on other networks unless taking price at a given timestamp or introduce some assumptions on scrvUSD behaviour.  
Hence, initial version named `v0` simply replicates scrvUSD and return real price at some timestamp.
Considering price is always growing, `v0` can be used as a lower bound.  
`v1` introduces assumption that noone interacts with scrvUSD further on.
This means that rewards being distributed as is, stopping at the end of period.
And no new deposits/withdrawals alter the rate.
This already gives a great assumption to the price over the distribution period,
because rate is more or less stable over 1-week period and small declines do not matter.  
`v2` adds an assumption that rewards denominated in crvUSD are equal through coming periods.
This is considered to approximate when rates are stable over long period of time,
especially when market is calm.

### Blockhash oracle

It is out of scope, so listing general assumptions:
1. It can be updated often enough with hash no older than, say, 30 minutes.
2. It can __rarely__ provide bad blockhash, but not a block number. So a new update with a fresh block number will fix parameters.

For curious readers, native blockhash feed solutions(like OP stack [pre-compile](https://optimistic.etherscan.io/address/0x4200000000000000000000000000000000000015#readProxyContract)) will be used with LayerZero for other networks as a "temporary" solution.

### Parameters

Spread from fee makes it impossible to manipulate the pool with changes up to the fee.
Taking minimum pool fee as 1bps it means that oracle should not jump more than 1 bps per block.
And for extra safety take 0.5bps as a safe threshold.  
Smoothening is introduced for sudden updates, so the price slowly catches up the price, while pool being arbitraged safely.
Though, smoothening limits the upper bound of price growth.
Therefore, we consider that scrvUSD will never be over 60% APR.

Also, good to note that oracle is controlled by DAO and parameters can be changed with a vote.


[Documentation](https://docs.curve.fi/scrvusd/overview/#smart-contracts)  
[GitHub](https://github.com/curvefi/storage-proofs/tree/audit)


## Actors

```
Actors:
    Prover: An offchain prover (from now on the prover), whose role is to fetch data from Ethereum that are useful to compute the growth rate of the vault, alongside with a proof that those data are valid.
    Verifier: A smart contract that will be called by the prover that will verify that the data provided alongside their proof.
    Oracle: A smart contract that will provide the current price of scrvUSD, given the growth rate of the vault provided by the prover and verified by the verifier, to be used by the stableswap-ng pool on the target chain.
    Blockhash oracle: A smart contract providing Ethereum blockhash or stateroot for verifying scrvUSD storage variables.
```

[//]: # (contest-details-close)

[//]: # (scope-open)

## Scope (contracts)

```
All Contracts in `contracts/scrvusd/` are in scope.
```
```js
contracts/
└── scrvusd/
    ├── oracles/
    │   └── ScrvusdOracleV2.vy
    └── verifiers/
        ├── ScrvusdVerifierV1.sol
        └── ScrvusdVerifierV2.sol
```

## Compatibilities

```
Compatibilities:
  Blockchains:
      - Any EVM, including solutions like neon on Solana
  Tokens:
      - scrvUSD
```

[//]: # (scope-close)

[//]: # (getting-started-open)

## Setup

Build:
```bash
# Install python dependencies using [uv](https://github.com/astral-sh/uv):

uv sync

# To enter the python environment:

source .venv/bin/activate

# Solidity dependencies:

solc-select install 0.8.18
solc-select use 0.8.18

npm install solidity-rlp@2.0.7

# Completely sync submodules and remove all unnecessary files:

git submodule update --init --recursive --depth 1
find contracts/xdao -mindepth 1 -maxdepth 1 ! -name 'contracts' -exec rm -rf {} +
find tests/scrvusd/contracts/scrvusd -depth -mindepth 1 ! -wholename 'tests/scrvusd/contracts/scrvusd/contracts/yearn/VaultV3.vy' -type f -delete
find tests/scrvusd/contracts/scrvusd -depth -type d -empty -delete
```

Tests:
```bash
pytest .

# Forked and slow stateful tests are disabled by default. To include them, use the --forked or --slow flags. For example:

pytest --slow
```

[//]: # (getting-started-close)

[//]: # (known-issues-open)

## Known Issues

None.

[//]: # (known-issues-close)
