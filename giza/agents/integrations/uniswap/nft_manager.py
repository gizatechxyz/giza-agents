import logging
import os
import time

from ape import Contract

from giza.agents.integrations.uniswap.constants import MAX_UINT_128
from giza.agents.integrations.uniswap.utils import (
    calc_amount0,
    calc_amount1,
    liquidity0,
    liquidity1,
    nearest_tick,
    price_to_sqrtp,
    price_to_tick,
)

logger = logging.getLogger(__name__)


class NFTManager:
    """
    Manages NFT-based liquidity positions on Uniswap via interaction with smart contracts.

    Attributes:
        contract (Contract): An instance of the Contract class representing the NFT manager smart contract.
        sender (str): The address of the user managing the NFT positions.
    """

    def __init__(self, address: str, sender: str):
        """
        Initializes the NFTManager with a specific contract address and sender.

        Args:
            address (str): The address of the NFT manager smart contract.
            sender (str): The address of the user managing the NFT positions.
        """
        self.contract = Contract(
            address,
            abi=os.path.join(os.path.dirname(__file__), "assets/nft_manager.json"),
        )
        self.sender = sender

    def get_all_user_positions(self, user_address: str | None = None):
        """
        Retrieves all NFT positions owned by a specified user.

        Args:
            user_address (str | None): The address of the user whose positions are to be retrieved.
                                       Defaults to the sender's address if None.

        Returns:
            list: A list of position identifiers owned by the user.
        """
        if user_address is None:
            user_address = self.sender
        n_positions = self.contract.balanceOf(user_address)
        positions = []
        for n in range(n_positions):
            position = self.contract.tokenOfOwnerByIndex(user_address, n)
            positions.append(position)
        return positions

    def close_position(self, nft_id: int, user_address: str | None = None):
        """
        Closes an NFT position by decreasing its liquidity to zero, collecting fees, and burning the NFT.

        Args:
            nft_id (int): The identifier of the NFT position to close.
            user_address (str | None): The address of the user closing the position.
                                       Defaults to the sender's address if None.
        """
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
        user_address: str | None = None,
        amount0_max: int | None = MAX_UINT_128,
        amount1_max: int | None = MAX_UINT_128,
    ):
        """
        Collects accumulated fees from a specified NFT position.

        Args:
            nft_id (int): The identifier of the NFT position from which to collect fees.
            user_address (str | None): The address of the user collecting the fees.
                                       Defaults to the sender's address if None.
            amount0_max (int | None): The maximum amount of token0 to collect.
                                      Defaults to the maximum uint128 value.
            amount1_max (int | None): The maximum amount of token1 to collect.
                                      Defaults to the maximum uint128 value.

        Returns:
            dict: A receipt of the transaction.
        """
        if user_address is None:
            user_address = self.sender
        logger.debug(f"Collecting fees for position {nft_id} for user {user_address}")
        receipt = self.contract.collect(
            (nft_id, user_address, amount0_max, amount1_max), sender=self.sender
        )
        logger.debug(f"Collected fees for position {nft_id} for user {user_address}")
        return receipt

    def decrease_liquidity(
        self,
        nft_id: int,
        liquidity: int | None = None,
        amount0Min: int | None = 0,
        amount1Min: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Decreases the liquidity of a specified NFT position.

        Args:
            nft_id (int): The identifier of the NFT position.
            liquidity (int | None): The amount of liquidity to remove. If None, fetches the current liquidity.
            amount0Min (int | None): The minimum amount of token0 that must remain after decreasing liquidity.
                                     Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must remain after decreasing liquidity.
                                     Defaults to 0.
            deadline (int | None): The Unix timestamp after which the transaction is no longer valid.
                                   Defaults to 60 seconds from the current time.

        Returns:
            dict: A receipt of the transaction.
        """
        if liquidity is None:
            liquidity = self.get_pos_info(nft_id)["liquidity"]
        if deadline is None:
            deadline = int(time.time() + 60)
        logger.debug(
            f"Decreasing liquidity for position {nft_id} for user {self.sender}"
        )
        receipt = self.contract.decreaseLiquidity(
            (nft_id, liquidity, amount0Min, amount1Min, deadline), sender=self.sender
        )
        logger.debug(
            f"Decreased liquidity for position {nft_id} for user {self.sender}"
        )
        return receipt

    def add_liquidity(
        self,
        nft_id: int,
        amount0Desired: int,
        amount1Desired: int,
        amount0Min: int | None = 0,
        amount1Min: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Adds liquidity to a specified NFT position.

        Args:
            nft_id (int): The identifier of the NFT position.
            amount0Desired (int): The desired amount of token0 to add.
            amount1Desired (int): The desired amount of token1 to add.
            amount0Min (int | None): The minimum amount of token0 that must be added. Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must be added. Defaults to 0.
            deadline (int | None): The Unix timestamp after which the transaction is no longer valid.
                                   Defaults to 60 seconds from the current time.

        Returns:
            dict: A receipt of the transaction.
        """
        pos = self.contract.positions(nft_id)
        token0 = Contract(
            pos["token0"],
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        token1 = Contract(
            pos["token1"],
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        # give allowances if needed
        if amount0Desired > token0.allowance(self.sender, self.contract.address):
            logger.debug(
                f"Approving {amount0Desired} tokens for {self.contract.address}"
            )
            token0.approve(self.contract.address, amount0Desired, sender=self.sender)
        if amount1Desired > token1.allowance(self.sender, self.contract.address):
            logger.debug(
                f"Approving {amount1Desired} tokens for {self.contract.address}"
            )
            token1.approve(self.contract.address, amount1Desired, sender=self.sender)

        if deadline is None:
            deadline = int(time.time() + 60)

        logger.debug(
            f"Increasing liquidity for position {nft_id} for user {self.sender}"
        )
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
        amount0Min: int | None = None,
        amount1Min: int | None = None,
        recipient: str | None = None,
        deadline: int | None = None,
        slippage_tolerance: float | None = 1,
    ):
        """
        Mints a new NFT position with specified parameters in a liquidity pool.

        Args:
            pool: The liquidity pool in which to mint the position.
            lower_price (float): The lower price boundary of the position.
            upper_price (float): The upper price boundary of the position.
            amount0 (int): The amount of token0 to be used.
            amount1 (int): The amount of token1 to be used.
            amount0Min (int | None): The minimum amount of token0 that must be added. Defaults to a calculated value based on slippage tolerance.
            amount1Min (int | None): The minimum amount of token1 that must be added. Defaults to a calculated value based on slippage tolerance.
            recipient (str | None): The recipient of the new position. Defaults to the sender's address if None.
            deadline (int | None): The Unix timestamp after which the transaction is no longer valid.
                                   Defaults to 60 seconds from the current time.
            slippage_tolerance (float | None): The tolerance for price slippage in percentage. Defaults to 1.

        Returns:
            dict: A receipt of the transaction.
        """
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
            logger.debug(f"Approving {amount0} tokens for {self.contract.address}")
            token0.approve(self.contract.address, amount0, sender=self.sender)
        if amount1 > token1.allowance(self.sender, self.contract.address):
            logger.debug(f"Approving {amount1} tokens for {self.contract.address}")
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

        logger.debug(
            f"Minting LP position with the following parameters: {mint_params}"
        )

        return self.contract.mint(mint_params, sender=self.sender)
