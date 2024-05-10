import os

from ape import Contract, chain

from .utils import tick_to_price


class Pool:
    def __init__(self, address, sender, token0=None, token1=None, fee=None):
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "ASSETS/pool.json")
        )
        self.sender = sender
        self.token0 = Contract(
            self.contract.token0(),
            abi=os.path.join(os.path.dirname(__file__), "ASSETS/erc20.json"),
        )
        self.token0_decimals = self.token0.decimals()
        self.token1 = Contract(
            self.contract.token1(),
            abi=os.path.join(os.path.dirname(__file__), "ASSETS/erc20.json"),
        )
        self.token1_decimals = self.token1.decimals()
        self.fee = self.contract.fee() if fee is None else fee

    def get_pool_info(self, block_number=None):
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
        ) = self.contract.slot0()
        return {
            "sqrtPriceX96": sqrtPriceX96,
            "tick": tick,
            "observationIndex": observationIndex,
            "observationCardinality": observationCardinality,
            "observationCardinalityNext": observationCardinalityNext,
            "feeProtocol": feeProtocol,
            "unlocked": unlocked,
        }

    def get_pool_price(self, block_number=None, invert=False):
        if block_number is None:
            block_number = chain.blocks.height
        tick = self.get_pool_info(block_number)["tick"]
        return tick_to_price(
            tick, self.token0_decimals, self.token1_decimals, invert=invert
        )
