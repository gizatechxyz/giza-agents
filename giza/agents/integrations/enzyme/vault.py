import os
from typing import Union

from ape import Contract


class Vault:
    def __init__(
        self, proxy_address: str, sender: str, comptroller_address: str | None = None
    ):
        self.vault_proxy = Contract(
            proxy_address,
            abi=os.path.join(os.path.dirname(__file__), "assets/vault_proxy.json"),
        )
        self.comptroller_proxy = (
            Contract(
                comptroller_address,
                abi=os.path.join(
                    os.path.dirname(__file__), "assets/comptroller_proxy.json"
                ),
            )
            if comptroller_address
            else Contract(
                self.vault_proxy.getAccessor(),
                abi=os.path.join(
                    os.path.dirname(__file__), "assets/comptroller_proxy.json"
                ),
            )
        )
        self.name = self.vault_proxy.name()
        self.symbol = self.vault_proxy.symbol()
        self.decimals = self.vault_proxy.decimals()
        self.denomination_asset = Contract(
            self.comptroller_proxy.getDenominationAsset()
        )
        self.denomination_asset_decimals = self.denomination_asset.decimals()

        self.sender = sender

    def get_timelock(self) -> int:
        return self.comptroller_proxy.getSharesActionTimelock()

    def get_total_shares(self):
        return self.vault_proxy.totalSupply() / 10**self.decimals

    def deposit(
        self,
        amount: Union[int, float],
        slippage: float | None = 0.01,
        simulate: bool | None = False,
    ):
        scaled_amount = int(
            (amount * 10**self.denomination_asset_decimals) * (1 - slippage)
        )
        if scaled_amount < self.denomination_asset.allowance(
            _owner=self.sender, _spender=self.comptroller_proxy
        ):
            self.denomination_asset.approve(
                self.comptroller_proxy, scaled_amount, sender=self.sender
            )
        if simulate:
            return self.comptroller_proxy.buyShares.call(
                scaled_amount, sender=self.sender
            )
        else:
            return self.comptroller_proxy.buyShares(scaled_amount, sender=self.sender)

    def redeem(
        self,
        shares_amount: int,
        payout_assets: list,
        payout_percentages: list,
        recipient: str | None = None,
        simulate: bool | None = False,
    ):
        """
        - payout_percentages is in bps
        - payout_assets - list of asset addresses
        """
        if recipient is None:
            recipient = self.sender

        # TODO: accept payout_percentages as q list of floats and parse the decimals here
        if simulate:
            return self.comptroller_proxy.redeemSharesForSpecificAssets.call(
                recipient,
                shares_amount,
                payout_assets,
                payout_percentages,
                sender=self.sender,
            )
        else:
            return self.comptroller_proxy.redeemSharesForSpecificAssets(
                recipient,
                shares_amount,
                payout_assets,
                payout_percentages,
                sender=self.sender,
            )

    # def get_tracked_assets(self) -> List[str]:
    #     return self.vault_proxy.getTrackedAssets()
    #
    # def get_external_positions(self) -> List[str]:
    #     return self.vault_proxy.getActiveExternalPositions()
