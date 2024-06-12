from ape.api import AccountAPI

from giza.agents.integrations import Uniswap


class IntegrationFactory:
    @staticmethod
    def from_name(name: str, sender: AccountAPI) -> Uniswap:
        match name:
            case "UniswapV3":
                return Uniswap(sender, version=3)
            case _:
                raise ValueError(f"Integration {name} not found")
