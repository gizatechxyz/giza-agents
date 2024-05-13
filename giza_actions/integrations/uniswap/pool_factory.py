import os

from ape import Contract

from giza_actions.integrations.uniswap.pool import Pool


class PoolFactory:
    def __init__(self, address: str, sender: str):
        self.contract = Contract(
            address,
            abi=os.path.join(os.path.dirname(__file__), "assets/pool_factory.json"),
        )
        self.sender = sender

    def get_pool(self, token0: str, token1: str, fee: int):
        if type(fee) == float:
            fee = int(fee * 1e6)
        pool_address = self.contract.getPool(token0, token1, fee)
        return Pool(pool_address, self.sender, token0=token0, token1=token1, fee=fee)

    def create_pool(self, token0: str, token1: str, fee: int):
        if type(fee) == float:
            fee = int(fee * 1e6)
        return self.contract.createPool(token0, token1, fee, sender=self.sender)
