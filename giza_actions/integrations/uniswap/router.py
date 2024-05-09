from ape import Contract
import os
import time


class Router:
    def __init__(self, address, sender):
        self.contract = Contract(address, abi = os.path.join(os.path.dirname(__file__), "ASSETS/router.json"))
        self.sender = sender

    def swap_exact_input_single(self, amount_in, pool=None, token_in=None, token_out=None, fee=None, amount_out_min=0, sqrt_price_limit_x96=0, deadline=None):
        if deadline is None:
            deadline = int(time.time()) + 60

        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")
        
        if (token_in is None or token_out is None or fee is None):
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
            "amountIn": amount_in,
            "amountOutMinimum": amount_out_min,
            "sqrtPriceLimitX96": sqrt_price_limit_x96,
        }

        return self.contract.exactInputSingle(swap_params, sender=self.sender)
    
    def swap_exact_output_single(self, amount_out, pool=None, token_in=None, token_out=None, fee=None, amount_in_max=0, sqrt_price_limit_x96=0, deadline=None):
        if deadline is None:
            deadline = int(time.time()) + 60

        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")
        
        if (token_in is None or token_out is None or fee is None):
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