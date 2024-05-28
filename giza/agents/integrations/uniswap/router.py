import os
import time

from ape import Contract

from giza.agents.integrations.uniswap.pool import Pool


class Router:
    def __init__(self, address: str, sender: str):
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "assets/router.json")
        )
        self.sender = sender

    def swap_exact_input_single(
        self,
        amount_in: int,
        pool: Pool = None,
        token_in: str = None,
        token_out: str = None,
        fee: int = None,
        amount_out_min: int = 0,
        sqrt_price_limit_x96: int = 0,
        deadline: int = None,
    ):

        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")

        if token_in is None or token_out is None or fee is None:
            token_in = pool.token0 if token_in is None else token_in
            token_out = pool.token1 if token_out is None else token_out
            fee = pool.fee if fee is None else fee

        if type(token_in)==str:
            token_in = Contract(token_in, abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"))

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

        return self.contract.exactInputSingle(swap_params, sender=self.sender)

    def swap_exact_output_single(
        self,
        amount_out: int,
        pool: Pool = None,
        token_in: str = None,
        token_out: str = None,
        fee: int = None,
        amount_in_max: int = 0,
        sqrt_price_limit_x96: int = 0,
        deadline: int = None,
    ):
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

        return self.contract.exactOutputSingle(swap_params, sender=self.sender)
