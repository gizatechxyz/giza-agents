import os
import time

from ape import Contract

from giza.agents.integrations.uniswap.constants import MAX_UINT_128
from giza.agents.integrations.uniswap.pool import Pool
from giza.agents.integrations.uniswap.utils import (
    calc_amount0,
    calc_amount1,
    liquidity0,
    liquidity1,
    nearest_tick,
    price_to_sqrtp,
    price_to_tick,
)


class NFTManager:
    def __init__(self, address: str, sender: str):
        self.contract = Contract(
            address,
            abi=os.path.join(os.path.dirname(__file__), "assets/nft_manager.json"),
        )
        self.sender = sender

    def get_all_user_positions(self, user_address: str = None):
        if user_address is None:
            user_address = self.sender
        n_positions = self.contract.balanceOf(user_address)
        positions = []
        for n in range(n_positions):
            position = self.contract.tokenOfOwnerByIndex(user_address, n)
            positions.append(position)
        return positions

    def close_position(self, nft_id: int, user_address: str = None):
        if user_address is None:
            user_address = self.sender
        liquidity = self.contract.positions(nft_id)["liquidity"]
        if liquidity > 0:
            self.decrease_liquidity(nft_id, liquidity=liquidity)
            self.collect_fees(nft_id, user_address=user_address)
            self.contract.burn(nft_id, sender=self.sender)

    def collect_fees(
        self,
        nft_id: int,
        user_address: str = None,
        amount0_max: int = MAX_UINT_128,
        amount1_max: int = MAX_UINT_128,
    ):
        if user_address is None:
            user_address = self.sender
        receipt = self.contract.collect(
            (nft_id, user_address, amount0_max, amount1_max), sender=self.sender
        )
        return receipt

    def decrease_liquidity(
        self,
        nft_id: int,
        liquidity: int = None,
        amount0Min: int = 0,
        amount1Min: int = 0,
        deadline: int = None,
    ):
        if liquidity is None:
            liquidity = self.get_pos_info(nft_id)["liquidity"]
        if deadline is None:
            deadline = int(time.time() + 60)
        receipt = self.contract.decreaseLiquidity(
            (nft_id, liquidity, amount0Min, amount1Min, deadline), sender=self.sender
        )
        return receipt

    def add_liquidity(
        self,
        nft_id: int,
        amount0Desired: int,
        amount1Desired: int,
        amount0Min: int = 0,
        amount1Min: int = 0,
        deadline: int = None,
    ):
        pos = self.contract.positions(nft_id)
        token0 = Contract(pos["token0"], abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"))
        token1 = Contract(pos["token1"], abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"))
        # give allowances if needed
        if amount0Desired > token0.allowance(self.sender, self.contract.address):
            token0.approve(self.contract.address, amount0Desired, sender=self.sender)
        if amount1Desired > token1.allowance(self.sender, self.contract.address):
            token1.approve(self.contract.address, amount1Desired, sender=self.sender)

        if deadline is None:
            deadline = int(time.time() + 60)

        receipt = self.contract.increaseLiquidity(
            (nft_id, amount0Desired, amount1Desired, amount0Min, amount1Min, deadline),
            sender=self.sender,
        )
        return receipt

    def mint_position(
        self,
        pool,
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
        fee = pool.fee
        token0 = pool.token0
        token0_decimals = token0.decimals()
        token1 = pool.token1
        token1_decimals = token1.decimals()

        lower_tick = price_to_tick(lower_price, token0_decimals, token1_decimals)
        upper_tick = price_to_tick(upper_price, token0_decimals, token1_decimals)
        lower_tick = nearest_tick(lower_tick, fee)
        upper_tick = nearest_tick(upper_tick, fee)

        if lower_tick > upper_tick:
            raise ValueError("Lower tick must be less than upper tick")

        sqrtp_cur = pool.get_pool_info()["sqrtPriceX96"]
        sqrtp_low = price_to_sqrtp(lower_price)
        sqrtp_upp = price_to_sqrtp(upper_price)
        liq0 = liquidity0(amount0, sqrtp_cur, sqrtp_upp)
        liq1 = liquidity1(amount1, sqrtp_cur, sqrtp_low)
        liq = int(min(liq0, liq1))
        amount0 = calc_amount0(liq, sqrtp_upp, sqrtp_cur)
        amount1 = calc_amount1(liq, sqrtp_low, sqrtp_cur)

        if amount0 > token0.allowance(self.sender, self.contract.address):
            token0.approve(self.contract.address, amount0, sender=self.sender)
        if amount1 > token1.allowance(self.sender, self.contract.address):
            token1.approve(self.contract.address, amount1, sender=self.sender)

        if recipient is None:
            recipient = self.sender
        if deadline is None:
            deadline = int(time.time() + 60)
        if amount0Min is None:
            amount0Min = int(amount0 * (1 - slippage_tolerance))
        if amount1Min is None:
            amount1Min = int(amount1 * (1 - slippage_tolerance))

        mint_params = {
            "token0": token0.address,
            "token1": token1.address,
            "fee": fee,
            "tickLower": lower_tick,
            "tickUpper": upper_tick,
            "amount0Desired": amount0,
            "amount1Desired": amount1,
            "amount0Min": amount0Min,
            "amount1Min": amount1Min,
            "recipient": recipient,
            "deadline": deadline,
        }

        return self.contract.mint(mint_params, sender=self.sender)
    