import logging

from giza.agents import GizaAgent


def transmission():
    logger = logging.getLogger(__name__)
    id = ...
    account = ...
    chain = "ethereum:mainnet-fork:foundry"
    agent = GizaAgent.from_id(
        integrations=["Enzyme"],
        contracts=None,
        id=id,
        chain=chain,
        account=account,
    )

    with agent.execute() as contracts:
        Diva_stETH_address = "0x1ce8aafb51e79f6bdc0ef2ebd6fd34b00620f6db"
        USDC_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        enzyme = contracts.Enzyme
        vault_tam = enzyme.get_vault_assets_value(Diva_stETH_address)
        vault_tam_usdc = enzyme.get_vault_assets_value(
            Diva_stETH_address, quote_asset=USDC_address
        )
        agent_vault_native_balance = enzyme.get_vault_share_value(Diva_stETH_address)
        agent_vault_usdc_balance = enzyme.get_vault_share_value(
            Diva_stETH_address, quote_asset=USDC_address
        )
        print(f"Vault TAM: {vault_tam['gav_']}")
        print(f"Vault TAM/USDC: {vault_tam_usdc}")
        print(
            f"Agent Vault Native Balance: {agent_vault_native_balance['grossShareValue_']}"
        )
        print(f"Agent Vault USDC Balance: {agent_vault_usdc_balance}")
        # prediction_result = result.value[0]
        ...
        agent_result = ...

        logger.info(f"agent_result: {agent_result}")

    logger.info("Finished")


transmission()
