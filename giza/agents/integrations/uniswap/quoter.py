import os

from ape import Contract
from ape.contracts import ContractInstance


class Quoter:
    def __init__(self, address: str, sender: str):
        self.contract = Contract(
            address, abi=os.path.join(os.path.dirname(__file__), "assets/quoter.json")
        )
        self.sender = sender

    def quote_exact_input_single(
        self,
        amount_in: int,
        pool: ContractInstance = None,
        token_in: str = None,
        token_out: str = None,
        fee: int = None,
        sqrt_price_limit_x96: int = 0,
        block_number: int = None,
    ):
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
