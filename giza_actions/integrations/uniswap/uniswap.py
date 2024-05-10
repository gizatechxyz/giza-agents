from ape import chain

from .addresses import ADDRESSES
from .nft_manager import NFTManager
from .pool_factory import PoolFactory
from .quoter import Quoter
from .router import Router


class Uniswap:
    def __init__(self, sender, version=3):
        self.sender = sender
        self._chain_id = chain.chain_id
        self.version = version
        self._load_contracts()

    def _load_contracts(self):
        if self.version == 2:
            # TODO
            pass
        elif self.version == 3:
            self.pool_factory = PoolFactory(
                ADDRESSES[self._chain_id][self.version]["PoolFactory"],
                sender=self.sender,
            )
            self.router = Router(
                ADDRESSES[self._chain_id][self.version]["Router"], sender=self.sender
            )
            self.quoter = Quoter(
                ADDRESSES[self._chain_id][self.version]["Quoter"], sender=self.sender
            )
            self.nft_manager = NFTManager(
                ADDRESSES[self._chain_id][self.version]["NonfungiblePositionManager"],
                sender=self.sender,
            )
        else:
            raise NotImplementedError(
                "Uniswap version {} not supported".format(self.version)
            )

    def print_addresses(self):
        print(f"PoolFactory: {self.pool_factory.contract.address}")
        print(f"Router: {self.router.contract.address}")
        print(f"Quoter: {self.quoter.contract.address}")
        print(f"NFT Manager: {self.nft_manager.contract.address}")

    def get_pool(self, token0, token1, fee):
        return self.pool_factory.get_pool(token0, token1, fee)
