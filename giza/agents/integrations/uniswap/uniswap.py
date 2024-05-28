from ape import chain, Contract
import os

from giza.agents.integrations.uniswap.constants import ADDRESSES, MAX_UINT_128
from giza.agents.integrations.uniswap.nft_manager import NFTManager
from giza.agents.integrations.uniswap.pool import Pool
from giza.agents.integrations.uniswap.pool_factory import PoolFactory
from giza.agents.integrations.uniswap.quoter import Quoter
from giza.agents.integrations.uniswap.router import Router


class Uniswap:
    def __init__(self, sender: str, version: int = 3):
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

    def get_pool(self, token0: str, token1: str, fee: int):
        return self.pool_factory.get_pool(token0, token1, fee)

    def create_pool(self, token0: str, token1: str, fee: int):
        return self.pool_factory.create_pool(token0, token1, fee)

    def get_all_user_positions(self, user_address: str = None):
        return self.nft_manager.get_all_user_positions(user_address=user_address)

    def get_pos_info(self, nft_id: int, block_number: str = None):
        if block_number is None:
            return self.nft_manager.contract.positions(nft_id)
        else:
            return self.nft_manager.contract.positions(
                nft_id, block_identifier=block_number
            )

    def close_position(self, nft_id: int, user_address: str = None):
        return self.nft_manager.close_position(nft_id, user_address=user_address)

    def collect_fees(
        self,
        nft_id: int,
        user_address: str = None,
        amount0_max: int = MAX_UINT_128,
        amount1_max: int = MAX_UINT_128,
    ):
        return self.nft_manager.collect_fees(
            nft_id,
            user_address=user_address,
            amount0_max=amount0_max,
            amount1_max=amount1_max,
        )

    def decrease_liquidity(
        self,
        nft_id: int,
        liquidity: int = None,
        amount0Min: int = 0,
        amount1Min: int = 0,
        deadline: int = None,
    ):
        return self.nft_manager.decrease_liquidity(
            nft_id,
            liquidity=liquidity,
            amount0Min=amount0Min,
            amount1Min=amount1Min,
            deadline=deadline,
        )

    def add_liquidity(
        self,
        nft_id: int,
        amount0_desired: int,
        amount1_desired: int,
        amount0Min: int = 0,
        amount1Min: int = 0,
        deadline: int = None,
    ):
        return self.nft_manager.add_liquidity(
            nft_id,
            amount0_desired,
            amount1_desired,
            amount0Min=amount0Min,
            amount1Min=amount1Min,
            deadline=deadline,
        )

    def mint_position(
        self,
        pool: Pool,
        lower_price: float,
        upper_price: float,
        amount0: int,
        amount1: int,
        amount0Min: int = None,
        amount1Min: int = None,
        recipient: str = None,
        deadline: int = None,
        slippage_tolerance: float = 1,
    ):
        self.nft_manager.mint_position(
            pool,
            lower_price=lower_price,
            upper_price=upper_price,
            amount0=amount0,
            amount1=amount1,
            amount0Min=amount0Min,
            amount1Min=amount1Min,
            recipient=recipient,
            deadline=deadline,
            slippage_tolerance=slippage_tolerance,
        )

    def rebalance_lp(
        self, 
        nft_id: int, 
        lower_price: float, 
        upper_price: float, 
        amount0Min: int = None,
        amount1Min: int = None,
        recipient: str = None,
        deadline: int = None,
        slippage_tolerance: float = 1,
    ):
        pos = self.nft_manager.contract.positions(nft_id)
        pool = self.get_pool(pos["token0"], pos["token1"], pos["fee"])

        token0 = Contract(pos["token0"], abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"))
        token1 = Contract(pos["token1"], abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"))
        self.nft_manager.close_position(nft_id)
        amount0 = token0.balanceOf(self.sender)
        amount1 = token1.balanceOf(self.sender)
        return self.nft_manager.mint_position(pool, lower_price, upper_price, amount0, amount1, amount0Min= amount0Min, amount1Min=amount1Min, recipient=recipient, deadline=deadline, slippage_tolerance=slippage_tolerance)
        

    def quote_exact_input_single(
        self,
        amount_in: int,
        pool: Pool = None,
        token_in: str = None,
        token_out: str = None,
        fee: int = None,
        sqrt_price_limit_x96: int = 0,
        block_number: int = None,
    ):
        return self.quoter.quote_exact_input_single(
            amount_in,
            pool=pool,
            token_in=token_in,
            token_out=token_out,
            fee=fee,
            sqrt_price_limit_x96=sqrt_price_limit_x96,
            block_number=block_number,
        )

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
        return self.router.swap_exact_input_single(
            amount_in=amount_in,
            pool=pool,
            token_in=token_in,
            token_out=token_out,
            fee=fee,
            amount_out_min=amount_out_min,
            sqrt_price_limit_x96=sqrt_price_limit_x96,
            deadline=deadline,
        )

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
        return self.router.swap_exact_output_single(
            amount_out=amount_out,
            pool=pool,
            token_in=token_in,
            token_out=token_out,
            fee=fee,
            amount_in_max=amount_in_max,
            sqrt_price_limit_x96=sqrt_price_limit_x96,
            deadline=deadline,
        )
