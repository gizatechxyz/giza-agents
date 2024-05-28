import os

from ape import Contract, accounts, networks
from dotenv import find_dotenv, load_dotenv
import logging

from giza.agents.integrations.uniswap.uniswap import Uniswap

load_dotenv(find_dotenv())
dev_passphrase = os.environ.get("DEV_PASSPHRASE")

logger = logging.getLogger(__name__)

with networks.parse_network_choice(f"ethereum:mainnet-fork:foundry"):
    sender = accounts.load("dev")
    sender.set_autosign(True, passphrase=dev_passphrase)

    weth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
    usdc_address = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    token0 = Contract(weth_address)
    token1 = Contract(usdc_address)
    fee = 500

    ### Uniswap ###
    uni = Uniswap(sender=sender, version=3)
    pool = uni.get_pool(token0, token1, fee)
    price = pool.get_pool_price(invert=True)
    logger.info(f"--------- Pool Price: {price}")

    ### Quoter ###
    amount_in = int(1e8)
    # calling using pool object
    amount_out = uni.quote_exact_input_single(amount_in, pool=pool)
    logger.info(f"--------- Amount out: {amount_out}")
    # # or by specifying the tokens and the fee
    amount_out = uni.quote_exact_input_single(
        amount_in, token_in=token1, token_out=token0, fee=fee
    )
    logger.info(f"--------- Amount out: {amount_out}")

    ### Router ###
    sender.balance += int(2e18)  # funding 1 eth more than we will use for gas
    token0.approve(sender, int(1e18), sender=sender)
    token0.deposit(value=int(1e18), sender=sender)
    token0_balance = token0.balanceOf(sender)
    logger.info(f"--------- Balances before swap: {token0_balance} {token1.balanceOf(sender)}")
    # token0.approve(uni.router.contract, token0_balance, sender=sender)
    uni.swap_exact_input_single(
        token0_balance, token_in=token0, token_out=token1, fee=fee
    )
    logger.info(
        f"--------- Balances after exactInputSingle swap: {token0.balanceOf(sender)} {token1.balanceOf(sender)}"
    )
    token1.approve(uni.router.contract, token1.balanceOf(sender), sender=sender)
    token0_amount_out = int(1e16)  # 0.01 eth
    accepted_slippage = 0.01  # 1%
    amount_in_max = int(token1.balanceOf(sender) * (1 - accepted_slippage))
    tx = uni.swap_exact_output_single(
        token0_amount_out,
        token_in=token1,
        token_out=token0,
        fee=fee,
        amount_in_max=amount_in_max,
    )
    logger.info(
        f"--------- Balances after exactOutputSingle swap: {token0.balanceOf(sender)} {token1.balanceOf(sender)}"
    )

    ### NFT Manager ###
    # token0.approve(uni.nft_manager.contract, token0.balanceOf(sender), sender=sender)
    # token1.approve(uni.nft_manager.contract, token1.balanceOf(sender), sender=sender)
    user_positions = uni.get_all_user_positions()
    logger.info(f"--------- User Positions Init: {user_positions}")
    amount0_to_mint = int(0.5 * token0.balanceOf(sender))
    amount1_to_mint = int(0.5 * token1.balanceOf(sender))
    price = pool.get_pool_price()
    pct_dev = 0.1
    lower_price = price * (1 - pct_dev)
    upper_price = price * (1 + pct_dev)
    uni.mint_position(
        pool,
        lower_price,
        upper_price,
        amount0=amount0_to_mint,
        amount1=amount1_to_mint,
        amount0Min=None,
        amount1Min=None,
        recipient=None,
        deadline=None,
        slippage_tolerance=1,
    )
    user_positions = uni.get_all_user_positions()
    price = pool.get_pool_price()
    logger.info(f"--------- User Positions after minting: {user_positions}")
    nft_id = user_positions[-1]
    pos_info = uni.get_pos_info(nft_id)
    logger.info(f"--------- {nft_id} Info: {pos_info}")
    increase_fraction = 0.1
    amount0_desired = int(amount0_to_mint * (1 + increase_fraction))
    amount1_desired = int(amount1_to_mint * (1 + increase_fraction))
    uni.add_liquidity(
        nft_id, amount0_desired, amount1_desired, amount0Min=0, amount1Min=0, deadline=None
    )
    pos_info = uni.get_pos_info(nft_id)
    logger.info(f"--------- {nft_id} Info Add Liq: {pos_info}")
    price = pool.get_pool_price()
    pct_dev = 0.5
    lower_price = price * (1 - pct_dev)
    upper_price = price * (1 + pct_dev)
    uni.rebalance_lp(nft_id, lower_price, upper_price)
    user_positions = uni.get_all_user_positions()
    nft_id = user_positions[-1]
    pos_info = uni.get_pos_info(nft_id)
    logger.info(f"--------- {nft_id} Info after rebalance: {pos_info}")
    uni.close_position(nft_id)
    user_positions = uni.get_all_user_positions()
    logger.info(f"--------- {nft_id} Burnt, user_pos: {user_positions}")
