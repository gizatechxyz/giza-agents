import os

from ape import Contract, chain

from giza.agents.integrations.uniswap.utils import tick_to_price


class Pool:
    """
    Represents a Uniswap pool, providing methods to interact with the pool's contract and fetch its details.

    Attributes:
        contract (Contract): The contract instance of the Uniswap pool.
        sender (str): The address of the sender interacting with the pool.
        token0 (Contract): The contract instance of the first token in the pool.
        token1 (Contract): The contract instance of the second token in the pool.
        token0_decimals (int): The number of decimals for the first token.
        token1_decimals (int): The number of decimals for the second token.
        fee (int): The fee associated with the pool transactions.
    """

    def __init__(
        self,
        address: str,
        sender: str,
        fee: int | None = None,
    ):
        """
        Initializes the Pool object with the specified address, sender, and optional fee.

        Args:
            address (str): The address of the Uniswap pool contract.
            sender (str): The address of the sender interacting with the pool.
            fee (int, optional): The fee associated with the pool. If None, the fee is fetched from the contract.
        """
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

    def get_pool_info(self, block_number: int | None = None):
        """
        Fetches and returns various operational details about the pool at a specific block number.

        Args:
            block_number (int, optional): The block number at which to fetch the pool details. Defaults to the current block height.

        Returns:
            dict: A dictionary containing details about the pool such as sqrtPriceX96, tick, observation indices, fee protocol, and unlocked status.
        """
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

    def get_pool_price(
        self, block_number: int | None = None, invert: bool | None = False
    ):
        """
        Calculates and returns the price of the pool based on the current tick, adjusted for token decimals and optionally inverted.

        Args:
            block_number (int, optional): The block number at which to fetch the tick for price calculation. Defaults to the current block height.
            invert (bool, optional): Whether to invert the price calculation. Defaults to False.

        Returns:
            float: The calculated price of the pool.
        """
        if block_number is None:
            block_number = chain.blocks.height
        tick = self.get_pool_info(block_number)["tick"]
        return tick_to_price(
            tick, self.token0_decimals, self.token1_decimals, invert=invert
        )
