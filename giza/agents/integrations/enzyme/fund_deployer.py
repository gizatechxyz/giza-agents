import os
import re

from ape import Contract, chain

from giza.agents.integrations.enzyme.constants import ADDRESSES


class FundDeployer:
    """
    A class responsible for deploying new funds on the Enzyme platform and retrieving information about existing funds.

    Attributes:
        contract (Contract): An instance of the Contract class to interact with the blockchain.
        sender (str): The address of the sender who is deploying the fund.

    Methods:
        create_fund(name, symbol, denomination_asset, shares_action_timelock_in_seconds, fee_manager_config_data, policy_manager_config_data, fund_owner=None):
            Deploys a new fund on the blockchain.

        get_vaults_list(start_block=0, end_block=0):
            Retrieves a list of vaults created within a specified block range.
    """

    def __init__(self, sender: str, chain_id: int | None = 1):
        """
        Initializes the FundDeployer with a specific blockchain contract and sender address.

        Args:
            sender (str): The address of the sender who will be deploying the fund.
            chain_id (int | None): The blockchain network ID. Defaults to 1 (Ethereum mainnet).
        """
        self.contract = Contract(
            ADDRESSES[chain_id]["fundDeployer"],
            abi=os.path.join(os.path.dirname(__file__), "assets/fund_deployer.json"),
        )
        self.sender = sender

    def create_fund(
        self,
        name: str,
        symbol: str,
        denomination_asset: str,
        shares_action_timelock_in_seconds: int,
        fee_manager_config_data: hex,
        policy_manager_config_data: hex,
        fund_owner: str | None = None,
    ) -> str:
        """
        Deploys a new fund on the blockchain.

        Args:
            name (str): The name of the fund.
            symbol (str): The trading symbol of the fund.
            denomination_asset (str): The asset used to denominate the fund.
            shares_action_timelock_in_seconds (int): The timelock duration for shares-related actions.
            fee_manager_config_data (hex): Configuration data for the fee manager.
            policy_manager_config_data (hex): Configuration data for the policy manager.
            fund_owner (str | None): The address of the fund owner. If None, the sender is used as the owner.

        Returns:
            str: The address of the newly created fund.
        """
        return self.contract.createNewFund(
            fund_owner,
            name,
            symbol,
            denomination_asset,
            shares_action_timelock_in_seconds,
            fee_manager_config_data,
            policy_manager_config_data,
            sender=self.sender,
        )

    def get_vaults_list(self, start_block: int = 0, end_block: int = 0):
        """
        Retrieves a list of vaults created within a specified block range.

        Args:
            start_block (int): The starting block number to query from. Defaults to 0.
            end_block (int): The ending block number to query to. If 0, uses the latest block number.

        Returns:
            list: A list of event arguments from the 'NewFundCreated' events within the specified block range.
        """
        start_block = 0
        if end_block == 0:
            end_block = chain.blocks[-1].number
        try:
            vaults_created = self.contract.NewFundCreated.query(
                "*",
                start_block=start_block,
                stop_block=end_block,
                engine_to_use="subsquid",
            )
        except Exception as e:
            try:
                last_integer = re.findall(r"\d+", e)[
                    -1
                ]  # Extracts all integers and picks the last one
                end_block = int(last_integer)
                vaults_created = self.contract.NewFundCreated.query(
                    "*",
                    start_block=start_block,
                    stop_block=end_block,
                    engine_to_use="subsquid",
                )
            except Exception as _:
                vaults_created = self.contract.NewFundCreated.query(
                    "*", start_block=start_block, stop_block=end_block
                )

        return vaults_created["event_arguments"].values
