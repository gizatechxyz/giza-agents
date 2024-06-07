from ape.api import AccountAPI

import giza.agents.integrations.uniswap.uniswap as uniswap_module


class IntegrationFactory:
    @staticmethod
    def from_name(name: str, sender: AccountAPI) -> uniswap_module.Uniswap:
        match name:
            case "UniswapV3":
                return uniswap_module.Uniswap(sender, version=3)
            case _:
                raise ValueError(f"Integration {name} not found")
