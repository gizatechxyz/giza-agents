import logging
import pprint

import numpy as np

from giza.agents import GizaAgent


def process_data(realized_vol, dec_price_change):
    pct_change_sq = (100 * dec_price_change) ** 2
    X = np.array([[realized_vol, pct_change_sq]])
    return X


def get_data():
    realized_vol = 4.20
    dec_price_change = 0.1
    return realized_vol, dec_price_change


def transmission():
    logger = logging.getLogger(__name__)
    id = ...
    version = ...
    account = ...
    realized_vol, dec_price_change = get_data()
    input_data = process_data(realized_vol, dec_price_change)

    agent = GizaAgent(
        integrations=["UniswapV3"],
        id=id,
        chain="ethereum:sepolia:geth",
        version_id=version,
        account=account,
    )

    result = agent.predict(
        input_feed={"val": input_data}, verifiable=True, dry_run=True
    )

    logger.info(f"Result: {result}")
    with agent.execute() as contracts:
        UNI_address = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
        WETH_address = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"
        uni = contracts.UniswapV3
        volatility_prediction = result.value[0]
        pool = uni.get_pool(UNI_address, WETH_address, fee=500)
        curr_price = pool.get_pool_price()
        lower_price = curr_price * (1 - volatility_prediction)
        upper_price = curr_price * (1 + volatility_prediction)
        amount0 = 100
        amount1 = 100
        agent_result = uni.mint_position(
            pool, lower_price, upper_price, amount0, amount1
        )
        logger.info(
            f"Current price: {curr_price}, new bounds: {lower_price}, {upper_price}"
        )
        logger.info(f"Minted position: {agent_result}")

    logger.info(f"Contract result: {agent_result}")
    logger.info("Finished")


transmission()
