from ape.api import AccountAPI

from giza.agents.integrations import Enzyme, Uniswap


class IntegrationFactory:
    @staticmethod
    def from_name(name: str, sender: AccountAPI) -> Uniswap:
        match name:
            case "UniswapV3":
                return Uniswap(sender, version=3)
            case "Enzyme":
                return Enzyme(sender)
            case _:
                raise ValueError(f"Integration {name} not found")
