import os
import pprint

import numpy as np
from addresses import ADDRESSES
from dotenv import find_dotenv, load_dotenv
from lp_tools import get_tick_range
from mint_position import close_position, get_all_user_positions, get_mint_params
from prefect import get_run_logger

from giza.agents.action import action
from giza.agents import AgentResult, GizaAgent
from giza.agents.task import task

load_dotenv(find_dotenv())

# Here we load a custom sepolia rpc url from the environment
sepolia_rpc_url = os.environ.get("SEPOLIA_RPC_URL")

MODEL_ID = ...  # Update with your model ID
VERSION_ID = ...  # Update with your version ID


@task(name="Data processing")
def process_data(realized_vol, dec_price_change):
    pct_change_sq = (100 * dec_price_change) ** 2
    X = np.array([[realized_vol, pct_change_sq]])

    return X


# Get image
@task(name="Get volatility and price change data")
def get_data():
    # TODO: implement fetching onchain or from some other source
    realized_vol = 4.20
    dec_price_change = 0.1
    return realized_vol, dec_price_change


@task(name="Create a Giza agent for the Volatility prediction model")
def create_agent(
    model_id: int, version_id: int, chain: str, contracts: dict, account: str
):
    """
    Create a Giza agent for the volatility prediction model
    """
    agent = GizaAgent(
        contracts=contracts,
        id=model_id,
        version_id=version_id,
        chain=chain,
        account=account,
    )
    return agent


@task(name="Predict the digit in an image.")
def predict(agent: GizaAgent, X: np.ndarray):
    """
    Predict the digit in an image.

    Args:
        image (np.ndarray): Image to predict.

    Returns:
        int: Predicted digit.
    """
    prediction = agent.predict(input_feed={"val": X}, verifiable=True, job_size="XL")
    return prediction


@task(name="Get the value from the prediction.")
def get_pred_val(prediction: AgentResult):
    """
    Get the value from the prediction.

    Args:
        prediction (dict): Prediction from the model.

    Returns:
        int: Predicted value.
    """
    # This will block the executon until the prediction has generated the proof and the proof has been verified
    return prediction.value[0][0]


# Create Action
@action(log_prints=True)
def transmission(
    pred_model_id,
    pred_version_id,
    account="dev",
    chain=f"ethereum:sepolia:{sepolia_rpc_url}",
):
    logger = get_run_logger()

    nft_manager_address = ADDRESSES["NonfungiblePositionManager"][11155111]
    tokenA_address = ADDRESSES["UNI"][11155111]
    tokenB_address = ADDRESSES["WETH"][11155111]
    pool_address = "0x287B0e934ed0439E2a7b1d5F0FC25eA2c24b64f7"
    user_address = "0xCBB090699E0664f0F6A4EFbC616f402233718152"

    pool_fee = 3000
    tokenA_amount = 1000
    tokenB_amount = 1000

    logger.info("Fetching input data")
    realized_vol, dec_price_change = get_data()

    logger.info(f"Input data: {realized_vol}, {dec_price_change}")
    X = process_data(realized_vol, dec_price_change)

    contracts = {
        "nft_manager": nft_manager_address,
        "tokenA": tokenA_address,
        "tokenB": tokenB_address,
        "pool": pool_address,
    }
    agent = create_agent(
        model_id=pred_model_id,
        version_id=pred_version_id,
        chain=chain,
        contracts=contracts,
        account=account,
    )
    result = predict(agent, X)
    predicted_value = get_pred_val(result)
    logger.info(f"Result: {result}")

    with agent.execute() as contracts:
        logger.info("Executing contract")
        # TODO: fix below
        positions = get_all_user_positions(contracts.nft_manager, user_address)
        logger.info(f"Found the following positions: {positions}")
        # step 4: close all positions
        logger.info("Closing all open positions...")
        for nft_id in positions:
            close_position(user_address, contracts.nft_manager, nft_id)
        # step 4: calculate mint params
        logger.info("Calculating mint params...")
        _, curr_tick, _, _, _, _, _ = contracts.pool.slot0()
        tokenA_decimals = contracts.tokenA.decimals()
        tokenB_decimals = contracts.tokenB.decimals()
        # TODO: confirm input should be result and not result * 100
        lower_tick, upper_tick = get_tick_range(
            curr_tick, predicted_value, tokenA_decimals, tokenB_decimals, pool_fee
        )
        mint_params = get_mint_params(
            user_address, tokenA_amount, tokenB_amount, pool_fee, lower_tick, upper_tick
        )
        # step 5: mint new position
        logger.info("Minting new position...")
        contract_result = contracts.nft_manager.mint(mint_params)
        logger.info("SUCCESSFULLY MINTED A POSITION")
        logger.info("Contract executed")

    logger.info(f"Contract result: {contract_result}")
    pprint.pprint(contract_result.__dict__)
    logger.info("Finished")


transmission(MODEL_ID, VERSION_ID)
