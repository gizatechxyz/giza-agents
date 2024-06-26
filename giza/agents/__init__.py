import logging
import pathlib

from giza.agents.agent import AgentResult, Contract, ContractHandler, GizaAgent

# The absolute path to this module
__module_path__ = pathlib.Path(__file__).parent
# The absolute path to the root of the repository, only valid for use during development
__development_base_path__ = __module_path__.parents[1]


def set_logging_level(level: int) -> None:
    """
    Set the logging level for the Giza package.

    Args:
        level (int): The logging level to set.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Set the log level for the root logger of the package
    logger = logging.getLogger("giza.agents")
    logger.setLevel(numeric_level)

    # Configure the logging handler
    handler = logging.StreamHandler()
    handler.setLevel(numeric_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(handler)


__all__ = ["GizaAgent", "AgentResult", "ContractHandler", "Contract"]
