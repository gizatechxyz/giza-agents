from ape import Contract
from .pool import Pool
import os

class PoolFactory:
    def __init__(self, address, sender):
        self.contract = Contract(address, abi = os.path.join(os.path.dirname(__file__), "ASSETS/pool_factory.json"))
        self.sender = sender

    def get_pool(self, token0, token1, fee):
        if type(fee)==float:
            fee = int(fee*1e6)
        pool_address = self.contract.getPool(token0, token1, fee)
        return Pool(pool_address, self.sender, token0=token0, token1=token1, fee=fee)

    
    def create_pool(self, token0, token1, fee):
        if type(fee)==float:
            fee = int(fee*1e6)
        return self.contract.createPool(token0, token1, fee, sender=self.sender)