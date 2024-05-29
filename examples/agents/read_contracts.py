"""
For this to work, we need to have the PASSPHRASE as an environment variable
This variable should have the form of "{ACCOUNT_ALIAS}_PASSPHRASE={PASSPHRASE}"

For example, if the ACCOUNT_ALIAS is "sepolia", then the environment variable should be "SEPOLIA_PASSPHRASE"

This is because the GizaAgent will look for the environment variable "{ACCOUNT_ALIAS}_PASSPHRASE" to allow auto signing

In this example, we instantiate the agent with the model id, version id, and the addresses of the contracts we want to interact with.
The contracts are stored in a dictionary where the key is the contract name and the value is the contract address.

We also specify the chain we want to interact with and the account alias we want to use to sign transactions, which, in this case is "sepolia".

To interact with the contracts, we use the execute method of the agent in a `with` block, so that the contracts will be available using the dot notation.
For example, if our agent has two contracts, "mnist" and "token", then we can access them using `contracts.mnist` and `contracts.token`, respectively.

In this example, we call the `name` method of the contracts, which is a method that returns the name of the contract, and then we print the result. But we could execute any function of a contract in the same way.
"""

from giza.agents import GizaAgent

MODEL_ID = ...
VERSION_ID = ...
ACCOUNT_ALIAS = ...

agent = GizaAgent(
    id=MODEL_ID,
    version_id=VERSION_ID,
    contracts={
        "mnist": "0x17807a00bE76716B91d5ba1232dd1647c4414912",
        "token": "0xeF7cCAE97ea69F5CdC89e496b0eDa2687C95D93B",
    },
    chain="ethereum:sepolia:geth",
    account=ACCOUNT_ALIAS,
)

with agent.execute() as contracts:
    result = contracts.mnist.name()
    print(result)
    result = contracts.token.name()
    print(result)
