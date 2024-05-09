from ape import Contract
import os

class Quoter:
    def __init__(self, address, sender):
        self.contract = Contract(address, abi=os.path.join(os.path.dirname(__file__), "ASSETS/quoter.json"))
        self.sender = sender

    def quote_exact_input_single(self, amount_in, pool=None, token_in=None, token_out=None, fee=None, sqrt_price_limit_x96=0):
        if pool is None and (token_in is None or token_out is None or fee is None):
            raise Exception("Must provide pool or token_in, token_out, and fee")
        
        if (token_in is None or token_out is None or fee is None):
            token_in = pool.token0 if token_in is None else token_in
            token_out = pool.token1 if token_out is None else token_out
            fee = pool.fee if fee is None else fee

        return self.contract.quoteExactInputSingle.call(token_in, token_out, fee, amount_in, sqrt_price_limit_x96)


