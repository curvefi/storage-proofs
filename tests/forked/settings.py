from enum import Enum
import os


# Using Chain ID for unique values
class Chain(Enum):
    ETH = 1
    OPTIMISM = 10
    BASE = 8453
    FRAXTAL = 252
    MANTLE = 5000
    ARBITRUM = 42161
    TAIKO = 167000
    SONIC = 146


CHAINS_DICT = {
    Chain.ETH: {
        "rpc": f"https://eth-mainnet.alchemyapi.io/v2/{os.environ['WEB3_ETHEREUM_MAINNET_ALCHEMY_PROJECT_ID']}",
    },
    Chain.OPTIMISM: {
        "rpc": "https://mainnet.optimism.io",
    },
    Chain.BASE: {"rpc": "https://mainnet.base.org"},
    Chain.FRAXTAL: {"rpc": "https://rpc.frax.com"},
    Chain.MANTLE: {"rpc": "https://rpc.mantle.xyz/"},
    Chain.ARBITRUM: {
        "rpc": "https://arb1.arbitrum.io/rpc",
    },
    Chain.TAIKO: {"rpc": "https://rpc.taiko.xyz"},
    Chain.SONIC: {"rpc": "https://rpc.soniclabs.com"},
}
