import os

from ape import Contract, chain

from giza_actions.integrations.uniswap.utils import tick_to_price


class Pool:
    def __init__(
        self,
        address: str,
        sender: str,
        token0: str = None,
        token1: str = None,
        fee: int = None,
    ):
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "assets/pool.json")
        )
        self.sender = sender
        self.token0 = Contract(
            self.contract.token0(),
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        self.token0_decimals = self.token0.decimals()
        self.token1 = Contract(
            self.contract.token1(),
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        self.token1_decimals = self.token1.decimals()
        self.fee = self.contract.fee() if fee is None else fee

    def get_pool_info(self, block_number: int = None):
        if block_number is None:
            block_number = chain.blocks.height
        (
            sqrtPriceX96,
            tick,
            observationIndex,
            observationCardinality,
            observationCardinalityNext,
            feeProtocol,
            unlocked,
        ) = self.contract.slot0(block_identifier=block_number)
        return {
            "sqrtPriceX96": sqrtPriceX96,
            "tick": tick,
            "observationIndex": observationIndex,
            "observationCardinality": observationCardinality,
            "observationCardinalityNext": observationCardinalityNext,
            "feeProtocol": feeProtocol,
            "unlocked": unlocked,
        }

    def get_pool_price(self, block_number: int = None, invert: bool = False):
        if block_number is None:
            block_number = chain.blocks.height
        tick = self.get_pool_info(block_number)["tick"]
        return tick_to_price(
            tick, self.token0_decimals, self.token1_decimals, invert=invert
        )
