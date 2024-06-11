import logging
import os
import time

from ape import Contract

from giza.agents.integrations.uniswap.pool import Pool

logger = logging.getLogger(__name__)


class Router:
    """
    A Router class to interact with the Uniswap contract for cryptocurrency swaps.

    Attributes:
        contract (Contract): An instance of the Contract class representing the Uniswap router contract.
        sender (str): The address of the sender initiating the swaps.

    Methods:
        swap_exact_input_single: Executes a swap where a precise input amount is specified.
        swap_exact_output_single: Executes a swap where a precise output amount is specified.
    """

    def __init__(self, address: str, sender: str):
        """
        Initializes the Router with a contract address and a sender address.

        Args:
            address (str): The address of the Uniswap router contract.
            sender (str): The address of the entity initiating the swaps.
        """
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "assets/router.json")
        )
        self.sender = sender

    def swap_exact_input_single(
        self,
        amount_in: int,
        pool: Pool | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        amount_out_min: int | None = 0,
        sqrt_price_limit_x96: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Executes a swap on Uniswap with an exact input amount specified.

        Args:
            amount_in (int): The amount of the input token to swap.
            pool (Pool, optional): The pool to perform the swap in. Defaults to None.
            token_in (str, optional): The address of the input token. Defaults to None.
            token_out (str, optional): The address of the output token. Defaults to None.
            fee (int, optional): The pool fee. Defaults to None.
            amount_out_min (int, optional): The minimum amount of the output token that must be received. Defaults to 0.
            sqrt_price_limit_x96 (int, optional): The price limit of the swap. Defaults to 0.
            deadline (int, optional): The timestamp after which the swap is invalid. Defaults to None.

        Raises:
            Exception: If necessary parameters are not provided.

        Returns:
            TransactionReceipt: A receipt of the swap transaction.
        """
        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")

        if token_in is None or token_out is None or fee is None:
            token_in = pool.token0 if token_in is None else token_in
            token_out = pool.token1 if token_out is None else token_out
            fee = pool.fee if fee is None else fee

        if isinstance(token_in, str):
            token_in = Contract(
                token_in,
                abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
            )

        if amount_in > token_in.allowance(self.sender, self.contract.address):
            token_in.approve(self.contract.address, amount_in, sender=self.sender)

        # TODO:
        # add slippage and pool price impact protection
        # if amount_out_min or sqrt_price_limit_x96 are floats

        if deadline is None:
            deadline = int(time.time()) + 60

        swap_params = {
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": fee,
            "recipient": self.sender,
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_min,
            "sqrtPriceLimitX96": sqrt_price_limit_x96,
        }

        logger.debug(f"Swapping with the following parameters: {swap_params}")

        return self.contract.exactInputSingle(swap_params, sender=self.sender)

    def swap_exact_output_single(
        self,
        amount_out: int,
        pool: Pool | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        amount_in_max: int | None = 0,
        sqrt_price_limit_x96: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Executes a swap on Uniswap with an exact output amount specified.

        Args:
            amount_out (int): The amount of the output token to receive.
            pool (Pool, optional): The pool to perform the swap in. Defaults to None.
            token_in (str, optional): The address of the input token. Defaults to None.
            token_out (str, optional): The address of the output token. Defaults to None.
            fee (int, optional): The pool fee. Defaults to None.
            amount_in_max (int, optional): The maximum amount of the input token that can be used. Defaults to 0.
            sqrt_price_limit_x96 (int, optional): The price limit of the swap. Defaults to 0.
            deadline (int, optional): The timestamp after which the swap is invalid. Defaults to None.

        Raises:
            Exception: If necessary parameters are not provided.

        Returns:
            TransactionReceipt: A receipt of the swap transaction.
        """
        if deadline is None:
            deadline = int(time.time()) + 60

        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")

        if token_in is None or token_out is None or fee is None:
            token_in = pool.token0 if token_in is None else token_in
            token_out = pool.token1 if token_out is None else token_out
            fee = pool.fee if fee is None else fee

        # TODO:
        # add slippage and pool price impact protection
        # if amount_out_min or sqrt_price_limit_x96 are floats

        swap_params = {
            "tokenIn": token_in,
            "tokenOut": token_out,
            "fee": fee,
            "recipient": self.sender,
            "deadline": deadline,
            "amountOut": amount_out,
            "amountInMaximum": amount_in_max,
            "sqrtPriceLimitX96": sqrt_price_limit_x96,
        }

        logger.debug(f"Swapping with the following parameters: {swap_params}")

        return self.contract.exactOutputSingle(swap_params, sender=self.sender)
