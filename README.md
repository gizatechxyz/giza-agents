
# Actions SDK

The Actions SDK is a Python library designed to facilitate the development of ZKML applications on the Giza platform. It provides a set of decorators and classes to define tasks, actions, and models, and to handle data inputs.

## Where to start?

Check out our extensive [documentation](https://actions.gizatech.xyz/welcome/giza-actions-sdk) to understand the concepts and follow how-to-guides.

## Installation

Start by creating a virtual environment in your project directory and activate it:

```bash
$ python -m venv .env

# Activate the virtual environment. On Linux and MacOs
$ source .env/bin/activate

# Activate Virtual environment on Windows:
$ .env/Scripts/activate
```

Now you’re ready to install ⚡Actions with the following command:

```bash
$ pip install giza-actions
```

## Setup

From your terminal, create a Giza user through our CLI in order to access the Giza Platform:

```bash
$ giza users create
```

After creating your user, log into Giza:

```bash
$ giza users login
```

Optional: you can create an API Key for your user in order to not regenerate your access token every few hours.

```bash
$ giza users create-api-key
```

To create Actions Runs you will need a Giza Workspace, create it by executing the following command in your terminal:

```bash
$ giza workspaces create
```

## Usage

### Defining Tasks

A task is a function that represents a distinct segment of work in a Giza Actions workflow. Tasks provide a way to encapsulate parts of your workflow logic in traceable, reusable units across actions.

Tasks are defined using the `@task` decorator. Here's an example:

```python
from giza.task import task

@task
def preprocess():
    print(f"Preprocessing...")
```

### Defining Actions

An action serves as a framework for coding ML inferencing workflow logic, enabling users to tailor the behaviour of their workflows.

Actions are defined using the `@action` decorator. Here's an example:

```python
from giza.action import action

@action(name="My Action")
def inference():
    print(f"Running inference...")
```

### Deploy Actions

Deployments are server-side representations of actions. They keep essential metadata required for remote orchestration, including when, where, and how a workflow should run. Deployments transform workflows from functions that need to be manually activated to API-managed entities capable of being triggered remotely.

We can easily create a deployment by creating the Action object and then calling the serve function in the entrypoint script:

```python
from giza_actions.action import Action, action
from giza_actions.task import task

@task
def print_hello():
    print(f"Hello Action!")

@action
def hello_world():
    print_hello()

if __name__ == '__main__':
    action_deploy = Action(entrypoint=hello_world, name="hello-world-action")
    action_deploy.serve(name="hello-world-action-deployment")
```

Running this script will do two things:

- Create a deployment called "hello-world-action" for your action in the Giza Platform.
- Stay running to listen for action runs for this deployment; when a run is found, it will be asynchronously executed within a subprocess locally.

### Creating Agents

Agents are the entities that interact with the Giza Platform to handle verification of predictions and interactions with Smart Contracts. They are responsible for wating until the proof of the prediction is available and verified, and then handling the interaction with the contract.

To create the agent, you will first need to locally create an [ape](https://apeworx.io/framework/) account:

```bash
$ ape accounts generate <account name>

Enhance the security of your account by adding additional random input:
Show mnemonic? [Y/n]: n
Create Passphrase to encrypt account:
Repeat for confirmation:
SUCCESS: A new account '0x766867bB2E3E1A6E6245F4930b47E9aF54cEba0C' with HDPath m/44'/60'/0'/0/0 has been added with the id '<account name>'
```

For more information on how to create an account, check the [ape documentation](https://docs.apeworx.io/ape/stable/userguides/accounts.html).

After creating the account, you can create the agent (**the agent must be associated with a version that has an existing endpoint**), this will prompt you to enter the account name:

```bash
$ giza agents create --model-id <model_id> --version-id <version_id> --name <agent_name> --description <agent_description>

[giza][2024-04-10 11:50:24.005] Creating agent ✅
[giza][2024-04-10 11:50:24.006] Using endpoint id to create agent, retrieving model id and version id
[giza][2024-04-10 11:50:53.480] Select an existing account to create the agent.
[giza][2024-04-10 11:50:53.480] Available accounts are:
┏━━━━━━━━━━━━━┓
┃  Accounts   ┃
┡━━━━━━━━━━━━━┩
│ my_account  │
└─────────────┘
Enter the account name: my_account
{
  "id": 1,
  "name": <agent_name>,
  "description": <agent_description>,
  "parameters": {
    "model_id": <model_id>,
    "version_id": <version_id>,
    "endpoint_id": <endpoint_id>,
    "alias": "my_account"
  },
  "created_date": "2024-04-10T09:51:04.226448",
  "last_update": "2024-04-10T09:51:04.226448"
}
```

Now, to interact with the agent and the contract, wou will need to export the passphrase of the account to the environment. The variable name should be `<ACCOUNT NAME>_PASSPHRASE`, all in caps. Make sure to keep this secret:

```bash
$ export <ACCOUNT NAME>_PASSPHRASE=<passphrase>
```

```python
from giza_actions.agent import Agent

# Here we check for the passphrase in the environment
agent = Agent.from_id(id=1, contracts={"my_contract": "0x1234567890"})

# Predict the data
result = agent.predict(data={"input": "data"})

# Handle the contracts
with agent.execute() as contracts:
    # Wait for the verification and then execute the contract
    contract_result = contracts.my_contract.function(result.value)

# Do anything with the result
...
```

## Examples

Examples of how to use the Actions SDK can be found in the `examples` directory. Each example includes a README or a Notebook with detailed instructions on how to run the example.

## Contributing

Contributions are welcome! Please submit a pull request or create an issue to get started.

## License

The Giza SDK is licensed under the MIT license.
