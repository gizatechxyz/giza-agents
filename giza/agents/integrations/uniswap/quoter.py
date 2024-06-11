import os

from ape import Contract
from ape.contracts import ContractInstance


class Quoter:
    """
    A class to interact with the Uniswap Quoter contract for obtaining quotes on token swaps.

    Attributes:
        contract (Contract): An instance of the Contract class representing the Uniswap Quoter contract.
        sender (str): The address of the sender initiating the quotes.

    Methods:
        __init__(self, address: str, sender: str): Initializes the Quoter instance.
        quote_exact_input_single(self, amount_in: int, pool: ContractInstance | None = None, token_in: str | None = None, token_out: str | None = None, fee: int | None = None, sqrt_price_limit_x96: int | None = 0, block_number: int | None = None): Provides a quote for a single input swap.
    """

    def __init__(self, address: str, sender: str):
        """
        Initializes the Quoter instance with a contract address and sender.

        Args:
            address (str): The address of the Uniswap Quoter contract.
            sender (str): The address of the entity initiating the quotes.
        """
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "assets/quoter.json")
        )
        self.sender = sender

    def quote_exact_input_single(
        self,
        amount_in: int,
        pool: ContractInstance | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        sqrt_price_limit_x96: int | None = 0,
        block_number: int | None = None,
    ):
        """
        Provides a quote for a single input swap based on the specified parameters.

        Args:
            amount_in (int): The amount of the input token.
            pool (ContractInstance | None): The contract instance of the pool. If None, token_in, token_out, and fee must be provided.
            token_in (str | None): The address of the input token. If None, it is derived from the pool.
            token_out (str | None): The address of the output token. If None, it is derived from the pool.
            fee (int | None): The pool's fee tier. If None, it is derived from the pool.
            sqrt_price_limit_x96 (int | None): The square root price limit of the swap, defaults to 0.
            block_number (int | None): The specific block number to execute the call against. If None, the latest block is used.

        Returns:
            The quote for the swap.

        Raises:
            Exception: If neither a pool nor the required individual parameters (token_in, token_out, fee) are provided.
        """
        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")

        if token_in is None or token_out is None or fee is None:
            token_in = pool.token0 if token_in is None else token_in
            token_out = pool.token1 if token_out is None else token_out
            fee = pool.fee if fee is None else fee

        if block_number is None:
            return self.contract.quoteExactInputSingle.call(
                token_in, token_out, fee, amount_in, sqrt_price_limit_x96
            )
        else:
            return self.contract.quoteExactInputSingle.call(
                token_in,
                token_out,
                fee,
                amount_in,
                sqrt_price_limit_x96,
                block_identifier=block_number,
            )
