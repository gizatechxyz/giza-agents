from giza.agents.integrations.enzyme.fund_calculator import FundCalculator
from giza.agents.integrations.enzyme.fund_deployer import FundDeployer
from giza.agents.integrations.enzyme.vault import Vault


class Enzyme:
    """
    The Enzyme class provides an interface to interact with the Enzyme protocol, allowing for the creation and management of investment funds on the blockchain.

    Attributes:
        chain_id (int | None): The blockchain network ID. Defaults to 1 (Ethereum mainnet).
        fund_deployer (FundDeployer): An instance of FundDeployer to handle fund deployment operations.
        fund_calculator (FundCalculator): An instance of FundCalculator to handle fund calculation operations.
        sender (str): The default sender address used for transactions.
    """

    def __init__(self, sender: str, chain_id: int | None = 1):
        """
        Initializes the Enzyme class with necessary components and default settings.

        Args:
            sender (str): The address that will be used as the default sender for transactions.
            chain_id (int | None): The ID of the blockchain network. Defaults to 1 (Ethereum mainnet).
        """
        self.chain_id = chain_id
        self.fund_deployer = FundDeployer(sender, self.chain_id)
        self.fund_calculator = FundCalculator(self.chain_id)
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
        Creates a new fund on the Enzyme platform.

        Args:
            name (str): The name of the fund.
            symbol (str): The symbol for the fund.
            denomination_asset (str): The asset used to denominate the fund.
            shares_action_timelock_in_seconds (int): The timelock duration for shares-related actions.
            fee_manager_config_data (hex): Configuration data for the fee manager.
            policy_manager_config_data (hex): Configuration data for the policy manager.
            fund_owner (str | None): The owner of the fund. Defaults to the sender if None.

        Returns:
            str: The address of the newly created fund.
        """
        if fund_owner is None:
            fund_owner = self.sender
        return self.fund_deployer.create_fund(
            name=name,
            symbol=symbol,
            denomination_asset=denomination_asset,
            shares_action_timelock_in_seconds=shares_action_timelock_in_seconds,
            fee_manager_config_data=fee_manager_config_data,
            policy_manager_config_data=policy_manager_config_data,
            fund_owner=fund_owner,
        )

    def get_vaults_list(self, start_block: int | None = 0, end_block: int | None = 0):
        """
        Retrieves a list of vaults created between specified block numbers.

        Args:
            start_block (int | None): The starting block number to search from. Defaults to 0.
            end_block (int | None): The ending block number to search to. Defaults to 0.

        Returns:
            list: A list of vault addresses.
        """
        return self.fund_deployer.get_vaults_list(
            start_block=start_block, end_block=end_block
        )

    def get_vault_assets_value(
        self,
        vault_proxy: str,
        quote_asset: str | None = None,
        net: bool | None = False,
        block_number: int | None = None,
    ):
        """
        Calculates the total value of assets in a specified vault.

        Args:
            vault_proxy (str): The address of the vault.
            quote_asset (str | None): The asset in which to quote the value. Defaults to None.
            net (bool | None): Whether to calculate net asset value. Defaults to False.
            block_number (int | None): The block number at which to evaluate the assets. Defaults to None.

        Returns:
            float: The total value of the assets in the specified vault.
        """
        return self.fund_calculator.get_assets_value(
            vault_proxy=vault_proxy,
            quote_asset=quote_asset,
            net=net,
            block_number=block_number,
        )

    def get_vault_share_value(
        self,
        vault_proxy: str,
        quote_asset: str | None = None,
        net: bool | None = False,
        shareholder: str | None = None,
        block_number: int | None = None,
    ):
        """
        Calculates the value of shares held by a shareholder in a specified vault.

        Args:
            vault_proxy (str): The address of the vault.
            quote_asset (str | None): The asset in which to quote the share value. Defaults to None.
            net (bool | None): Whether to calculate net share value. Defaults to False.
            shareholder (str | None): The address of the shareholder. Defaults to None.
            block_number (int | None): The block number at which to evaluate the shares. Defaults to None.

        Returns:
            float: The value of the shares held by the specified shareholder.
        """
        return self.fund_calculator.get_share_value(
            vault_proxy=vault_proxy,
            quote_asset=quote_asset,
            net=net,
            shareholder=shareholder,
            block_number=block_number,
        )

    def load_vault(self, vault_proxy: str, comptroller_address: str | None = None):
        return Vault(
            proxy_address=vault_proxy,
            sender=self.sender,
            comptroller_address=comptroller_address,
        )
