from typing import List, Optional

from pydantic import BaseModel

from giza_datasets.defillama_constants import DEFILLAMA_SUPPORTED_PROJECTS

sector_tags = ["DeFi"]
application_tags = ["Liquid Staking", "Dexes", "Yield", "Lending", "Yield Aggregator"]
protocol_tags = DEFILLAMA_SUPPORTED_PROJECTS + [
    "Aave-v2",
    "Aave-v3",
    "Compound-v2",
    "Balancer-v1",
    "Balancer-v2",
    "MorphoBlue",
    "Uniswap-v3",
    "Yearn-v2",
]
network_tags = [
    "Ethereum",
    "Arbitrum",
    "Optimism",
    "Avalanche",
    "Base",
    "Gnosis",
    "Polygon",
    "multi-chain",
]
task_tags = [
    "TVL",
    "Token Price",
    "Swap Fees",
    "Liquidity",
    "Borrows & Deposits",
    "Trade Volume",
    "Fees",
    "APY",
    "daily",
    "aggregated",
    "Deposits",
    "Withdraws",
    "Liquiditations",
    "Mcap",
]


class Dataset(BaseModel):
    """
    A Pydantic model representing a Dataset.

    Attributes:
        name (str): The name of the dataset.
        path (str): The path to the dataset.
        description (str): A brief description of the dataset.
        labels Optional[List[str]]: Optional, predefined list of labels associated with the dataset.
        documentation (str): The documentation associated with the dataset.
    """

    name: str
    path: str
    description: str
    tags: Optional[List[str]]
    documentation: str
