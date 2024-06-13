import os

from ape import Contract, chain

from giza.agents.integrations.enzyme.constants import ADDRESSES


class FundCalculator:
    """
    A class to calculate various financial metrics for funds managed through the Enzyme protocol.

    Attributes:
        contract (Contract): An instance of the Contract class to interact with the blockchain.

    Methods:
        get_assets_value(vault_proxy, quote_asset=None, net=False, block_number=None):
            Calculate the value of assets in a vault, either as NAV (Net Asset Value) or GAV (Gross Asset Value).

        get_share_value(vault_proxy, quote_asset=None, net=False, shareholder=None, block_number=None):
            Calculate the value of shares in a vault, either net or gross, optionally for a specific shareholder.
    """

    def __init__(self, chain_id: int | None = 1):
        """
        Initializes the FundCalculator with a specific blockchain contract.

        Args:
            chain_id (int | None): The blockchain network ID. Defaults to 1 (Starknet mainnet).
        """
        self.contract = Contract(
            ADDRESSES[chain_id]["fundValueCalculatorRouter"],
            abi=os.path.join(
                os.path.dirname(__file__), "assets/fund_value_calculator_router.json"
            ),
        )

    def get_assets_value(
        self,
        vault_proxy: str,
        quote_asset: str | None = None,
        net: bool | None = False,
        block_number: int | None = None,
    ):
        """
        Retrieves the value of assets managed by a vault.

        Args:
            vault_proxy (str): The address of the vault proxy.
            quote_asset (str | None): The asset in which the value should be quoted. If None, defaults to the vault's base asset.
            net (bool | None): If True, returns the Net Asset Value (NAV); otherwise, returns the Gross Asset Value (GAV).
            block_number (int | None): The block number at which to fetch the value. If None, uses the latest block.

        Returns:
            Union[int, float]: The calculated asset value.
        """
        if block_number is None:
            block_number = chain.blocks[-1].number

        if quote_asset is None:
            if net:
                return self.contract.calcNav.call(
                    vault_proxy, block_identifier=block_number
                )
            else:
                return self.contract.calcGav.call(
                    vault_proxy, block_identifier=block_number
                )
        else:
            if net:
                return self.contract.calcNavInAsset.call(
                    vault_proxy, quote_asset, block_identifier=block_number
                )
            else:
                return self.contract.calcGavInAsset.call(
                    vault_proxy, quote_asset, block_identifier=block_number
                )

    def get_share_value(
        self,
        vault_proxy: str,
        quote_asset: str | None = None,
        net: bool | None = False,
        shareholder: str | None = None,
        block_number: int | None = None,
    ):
        """
        Retrieves the value of shares held in a vault.

        Args:
            vault_proxy (str): The address of the vault proxy.
            quote_asset (str | None): The asset in which the share value should be quoted. If None, defaults to the vault's base asset.
            net (bool | None): If True, returns the net share value; otherwise, returns the gross share value.
            shareholder (str | None): The address of the shareholder. If None, calculates for the total shares.
            block_number (int | None): The block number at which to fetch the value. If None, uses the latest block.

        Returns:
            Union[int, float]: The calculated share value.
        """
        if block_number is None:
            block_number = chain.blocks[-1].number

        if quote_asset is None:
            if net:
                if shareholder is None:
                    return self.contract.calcNetShareValue.call(
                        vault_proxy, block_identifier=block_number
                    )
                else:
                    return self.contract.calcNetValueForSharesHolder.call(
                        vault_proxy, shareholder, block_identifier=block_number
                    )
            else:
                if shareholder is None:
                    return self.contract.calcGrossShareValue.call(
                        vault_proxy, block_identifier=block_number
                    )
                else:
                    return self.contract.calcGrossValueForSharesHolder.call(
                        vault_proxy, shareholder, block_identifier=block_number
                    )

        else:
            if net:
                if shareholder is None:
                    return self.contract.calcNetShareValueInAsset.call(
                        vault_proxy, quote_asset, block_identifier=block_number
                    )
                else:
                    return self.contract.calcNetValueForSharesHolderInAsset.call(
                        vault_proxy,
                        quote_asset,
                        shareholder,
                        block_identifier=block_number,
                    )
            else:
                if shareholder is None:
                    return self.contract.calcGrossShareValueInAsset.call(
                        vault_proxy, quote_asset, block_identifier=block_number
                    )
                else:
                    return self.contract.calcGrossValueForSharesHolderInAsset.call(
                        vault_proxy,
                        quote_asset,
                        shareholder,
                        block_identifier=block_number,
                    )
