import logging
import os

from ape import Contract

from giza.agents.integrations.uniswap.pool import Pool

logger = logging.getLogger(__name__)


class PoolFactory:
    """
    A factory class for managing Uniswap pool interactions.

    Attributes:
        contract (Contract): An instance of the Contract class to interact with the Uniswap pool factory.
        sender (str): The address of the transaction sender.

    Methods:
        __init__(self, address: str, sender: str): Initializes a new PoolFactory instance.
        get_pool(self, token0: str, token1: str, fee: int): Retrieves a pool based on the provided tokens and fee.
        create_pool(self, token0: str, token1: str, fee: int): Creates a new pool with the specified tokens and fee.
    """

    def __init__(self, address: str, sender: str):
        """
        Initializes a new instance of the PoolFactory class.

        Args:
            address (str): The address of the Uniswap pool factory contract.
            sender (str): The address of the entity initiating transactions.
        """
        self.contract = Contract(
            address,
            abi=os.path.join(os.path.dirname(__file__), "assets/pool_factory.json"),
        )
        self.sender = sender

    def get_pool(self, token0: str, token1: str, fee: int):
        """
        Retrieves the address of a Uniswap pool for the specified tokens and fee.

        Args:
            token0 (str): The address of the first token.
            token1 (str): The address of the second token.
            fee (int): The pool fee in integer format. If a float is provided, it is converted to an integer.

        Returns:
            Pool: An instance of the Pool class representing the retrieved pool.
        """
        if isinstance(fee, float):
            fee = int(fee * 1e6)
        pool_address = self.contract.getPool(token0, token1, fee)
        return Pool(pool_address, self.sender)

    def create_pool(self, token0: str, token1: str, fee: int):
        """
        Creates a new Uniswap pool with the specified tokens and fee.

        Args:
            token0 (str): The address of the first token.
            token1 (str): The address of the second token.
            fee (int): The pool fee in integer format. If a float is provided, it is converted to an integer.

        Returns:
            The result of the pool creation transaction.
        """
        if isinstance(fee, float):
            fee = int(fee * 1e6)
        logger.debug(
            f"Creating pool with token0 {token0}, token1 {token1}, and fee {fee}"
        )
        return self.contract.createPool(token0, token1, fee, sender=self.sender)
