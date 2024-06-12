import os

from ape import Contract, chain

from giza.agents.integrations.uniswap.constants import ADDRESSES, MAX_UINT_128
from giza.agents.integrations.uniswap.nft_manager import NFTManager
from giza.agents.integrations.uniswap.pool import Pool
from giza.agents.integrations.uniswap.pool_factory import PoolFactory
from giza.agents.integrations.uniswap.quoter import Quoter
from giza.agents.integrations.uniswap.router import Router


class Uniswap:
    """
    A class to interact with the Uniswap protocol, supporting various operations such as
    liquidity management, swapping, and quoting for different versions of the protocol.

    Attributes:
        sender (str): The address initiating transactions.
        version (int): The version of the Uniswap protocol to interact with.
        _chain_id (int): The chain ID of the current blockchain.
        pool_factory (PoolFactory): The factory class for pool-related operations.
        router (Router): The router class for swap-related operations.
        quoter (Quoter): The quoter class for price quote-related operations.
        nft_manager (NFTManager): The manager class for non-fungible token positions.
    """

    def __init__(self, sender: str, version: int = 3):
        """
        Initializes the Uniswap class with a sender address and protocol version.

        Args:
            sender (str): The address that will be used as the sender for transactions.
            version (int, optional): The version of the Uniswap protocol. Defaults to 3.
        """
        self.sender = sender
        self._chain_id = chain.chain_id
        self.version = version
        self._load_contracts()

    def _load_contracts(self):
        """
        Loads the necessary contracts based on the Uniswap version specified.
        Raises NotImplementedError if the version is not supported.
        """
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
        """
        Retrieves a pool based on the provided token addresses and fee tier.

        Args:
            token0 (str): The address of the first token.
            token1 (str): The address of the second token.
            fee (int): The fee tier of the pool.

        Returns:
            Pool: The pool object corresponding to the specified tokens and fee.
        """
        return self.pool_factory.get_pool(token0, token1, fee)

    def create_pool(self, token0: str, token1: str, fee: int):
        """
        Creates a new liquidity pool for the specified token pair and fee tier.

        Args:
            token0 (str): The address of the first token.
            token1 (str): The address of the second token.
            fee (int): The fee tier for the new pool.

        Returns:
            Pool: The newly created pool object.
        """
        return self.pool_factory.create_pool(token0, token1, fee)

    def get_all_user_positions(self, user_address: str | None = None):
        """
        Retrieves all positions for a given user address.

        Args:
            user_address (str | None): The address of the user. If None, uses the sender's address.

        Returns:
            list: A list of all positions held by the user.
        """
        return self.nft_manager.get_all_user_positions(user_address=user_address)

    def get_pos_info(self, nft_id: int, block_number: str | None = None):
        """
        Retrieves position information for a specific NFT ID, optionally at a specific block number.

        Args:
            nft_id (int): The NFT ID of the position.
            block_number (str | None): The block number at which to retrieve the position info. If None, uses the latest block.

        Returns:
            dict: The position information.
        """
        if block_number is None:
            return self.nft_manager.contract.positions(nft_id)
        else:
            return self.nft_manager.contract.positions(
                nft_id, block_identifier=block_number
            )

    def close_position(self, nft_id: int, user_address: str | None = None):
        """
        Closes a position for a given NFT ID, optionally for a specific user address.

        Args:
            nft_id (int): The NFT ID of the position to close.
            user_address (str | None): The address of the user. If None, uses the sender's address.

        Returns:
            bool: True if the position was successfully closed, False otherwise.
        """
        return self.nft_manager.close_position(nft_id, user_address=user_address)

    def collect_fees(
        self,
        nft_id: int,
        user_address: str | None = None,
        amount0_max: int | None = MAX_UINT_128,
        amount1_max: int | None = MAX_UINT_128,
    ):
        """
        Collects accumulated fees for a given position.

        Args:
            nft_id (int): The NFT ID of the position.
            user_address (str | None): The address of the user. If None, uses the sender's address.
            amount0_max (int | None): The maximum amount of token0 to collect. Defaults to MAX_UINT_128.
            amount1_max (int | None): The maximum amount of token1 to collect. Defaults to MAX_UINT_128.

        Returns:
            dict: The amounts of token0 and token1 collected.
        """
        return self.nft_manager.collect_fees(
            nft_id,
            user_address=user_address,
            amount0_max=amount0_max,
            amount1_max=amount1_max,
        )

    def decrease_liquidity(
        self,
        nft_id: int,
        liquidity: int | None = None,
        amount0Min: int | None = 0,
        amount1Min: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Decreases the liquidity of a given position.

        Args:
            nft_id (int): The NFT ID of the position.
            liquidity (int | None): The amount of liquidity to remove. If None, removes all liquidity.
            amount0Min (int | None): The minimum amount of token0 that must be returned. Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must be returned. Defaults to 0.
            deadline (int | None): The deadline by which the transaction must be confirmed. If None, no deadline is set.

        Returns:
            dict: The amounts of token0 and token1 returned after decreasing liquidity.
        """
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
        amount0Min: int | None = 0,
        amount1Min: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Adds liquidity to a given position.

        Args:
            nft_id (int): The NFT ID of the position.
            amount0_desired (int): The desired amount of token0 to add.
            amount1_desired (int): The desired amount of token1 to add.
            amount0Min (int | None): The minimum amount of token0 that must be added. Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must be added. Defaults to 0.
            deadline (int | None): The deadline by which the transaction must be confirmed. If None, no deadline is set.

        Returns:
            dict: The actual amounts of token0 and token1 added to the position.
        """
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
        amount0Min: int | None = None,
        amount1Min: int | None = None,
        recipient: str | None = None,
        deadline: int | None = None,
        slippage_tolerance: float | None = 1,
    ):
        """
        Mints a new position or increases liquidity in an existing position within specified price bounds.

        Args:
            pool (Pool): The pool in which to mint the position.
            lower_price (float): The lower price bound of the position.
            upper_price (float): The upper price bound of the position.
            amount0 (int): The amount of token0 to be added.
            amount1 (int): The amount of token1 to be added.
            amount0Min (int | None): The minimum amount of token0 that must be added. Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must be added. Defaults to 0.
            recipient (str | None): The recipient of the position. If None, defaults to the sender.
            deadline (int | None): The deadline by which the transaction must be confirmed. If None, no deadline is set.
            slippage_tolerance (float | None): The maximum acceptable slippage percentage. Defaults to 1.

        Returns:
            dict: Details of the minted position.
        """
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
        amount0Min: int | None = None,
        amount1Min: int | None = None,
        recipient: str | None = None,
        deadline: int | None = None,
        slippage_tolerance: float | None = 1,
    ):
        """
        Rebalances a liquidity position by closing the current position and minting a new one with updated parameters.

        Args:
            nft_id (int): The NFT ID of the position to rebalance.
            lower_price (float): The new lower price bound for the position.
            upper_price (float): The new upper price bound for the position.
            amount0Min (int | None): The minimum amount of token0 that must be returned from the closed position. Defaults to 0.
            amount1Min (int | None): The minimum amount of token1 that must be returned from the closed position. Defaults to 0.
            recipient (str | None): The recipient of the new position. If None, defaults to the sender.
            deadline (int | None): The deadline by which the transaction must be confirmed. If None, no deadline is set.
            slippage_tolerance (float | None): The maximum acceptable slippage percentage. Defaults to 1.

        Returns:
            dict: Details of the rebalanced position.
        """
        pos = self.nft_manager.contract.positions(nft_id)
        pool = self.get_pool(pos["token0"], pos["token1"], pos["fee"])

        token0 = Contract(
            pos["token0"],
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        token1 = Contract(
            pos["token1"],
            abi=os.path.join(os.path.dirname(__file__), "assets/erc20.json"),
        )
        self.nft_manager.close_position(nft_id)
        amount0 = token0.balanceOf(self.sender)
        amount1 = token1.balanceOf(self.sender)
        return self.nft_manager.mint_position(
            pool,
            lower_price,
            upper_price,
            amount0,
            amount1,
            amount0Min=amount0Min,
            amount1Min=amount1Min,
            recipient=recipient,
            deadline=deadline,
            slippage_tolerance=slippage_tolerance,
        )

    def quote_exact_input_single(
        self,
        amount_in: int,
        pool: Pool | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        sqrt_price_limit_x96: int | None = 0,
        block_number: int | None = None,
    ):
        """
        Provides a quote for a given input amount for a single swap operation in a specified pool.

        Args:
            amount_in (int): The amount of the input token to be swapped.
            pool (Pool | None): The pool object to perform the swap. If None, pool is determined by token addresses and fee.
            token_in (str | None): The address of the input token. Required if pool is None.
            token_out (str | None): The address of the output token. Required if pool is None.
            fee (int | None): The fee tier of the pool. Required if pool is None.
            sqrt_price_limit_x96 (int | None): The price limit of the swap as a sqrt price. Defaults to 0 (no limit).
            block_number (int | None): The block number at which the quote should be fetched. If None, uses the latest block.

        Returns:
            dict: A dictionary containing the estimated output amount and other relevant swap details.
        """
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
        pool: Pool | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        amount_out_min: int | None = 0,
        sqrt_price_limit_x96: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Executes a swap from an exact input amount to a minimum output amount in a specified pool.

        Args:
            amount_in (int): The exact amount of the input token to be swapped.
            pool (Pool | None): The pool object to perform the swap. If None, pool is determined by token addresses and fee.
            token_in (str | None): The address of the input token. Required if pool is None.
            token_out (str | None): The address of the output token. Required if pool is None.
            fee (int | None): The fee tier of the pool. Required if pool is None.
            amount_out_min (int | None): The minimum amount of the output token that must be received. Defaults to 0.
            sqrt_price_limit_x96 (int | None): The price limit of the swap as a sqrt price. Defaults to 0 (no limit).
            deadline (int | None): The timestamp by which the transaction must be confirmed. If None, no deadline is set.

        Returns:
            dict: A dictionary containing the actual output amount and other relevant swap details.
        """
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
        pool: Pool | None = None,
        token_in: str | None = None,
        token_out: str | None = None,
        fee: int | None = None,
        amount_in_max: int | None = 0,
        sqrt_price_limit_x96: int | None = 0,
        deadline: int | None = None,
    ):
        """
        Executes a swap to receive an exact output amount, specifying a maximum input amount in a specified pool.

        Args:
            amount_out (int): The exact amount of the output token to be received.
            pool (Pool | None): The pool object to perform the swap. If None, pool is determined by token addresses and fee.
            token_in (str | None): The address of the input token. Required if pool is None.
            token_out (str | None): The address of the output token. Required if pool is None.
            fee (int | None): The fee tier of the pool. Required if pool is None.
            amount_in_max (int | None): The maximum amount of the input token that can be used. Defaults to 0.
            sqrt_price_limit_x96 (int | None): The price limit of the swap as a sqrt price. Defaults to 0 (no limit).
            deadline (int | None): The timestamp by which the transaction must be confirmed. If None, no deadline is set.

        Returns:
            dict: A dictionary containing the actual input amount used and other relevant swap details.
        """
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
