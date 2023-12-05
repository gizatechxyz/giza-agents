import json
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel


# Define your Pydantic models
class JobVariables(BaseModel):
    image: str


class WorkPool(BaseModel):
    name: str
    work_queue_name: Optional[str] = "default"
    job_variables: JobVariables


class DeploymentStep(BaseModel):
    prefect_deployments_steps_set_working_directory: Dict[str, str]


class Deployment(BaseModel):
    name: str
    version: Optional[str] = None
    tags: Optional[List[str]] = []
    description: Optional[str] = None
    schedule: Optional[str] = None
    entrypoint: str
    parameters: Optional[Dict] = {}
    work_pool: WorkPool
    pull: List[DeploymentStep]


class ActionDeployment(BaseModel):
    name: str
    prefect_version: str
    deployments: List[Deployment]


# Function to create the project object
def create_action_deployment(
    name: str,
    prefect_version: str,
    deployment_name: str,
    entrypoint: str,
    pool_name: str,
    image: str,
) -> ActionDeployment:
    return ActionDeployment(
        name=name,
        prefect_version=prefect_version,
        deployments=[
            Deployment(
                name=deployment_name,
                entrypoint=entrypoint,
                work_pool=WorkPool(
                    name=pool_name, job_variables=JobVariables(image=image)
                ),
                pull=[
                    DeploymentStep(
                        prefect_deployments_steps_set_working_directory={
                            "directory": "/opt/prefect"
                        }
                    )
                ],
            )
        ],
    )


# Function to save the project data as a YAML file
def save_action_deployment_as_yaml(project: ActionDeployment, filename: str):
    # Convert Pydantic object to JSON, then load it into a Python dictionary
    project_dict = json.loads(project.json())

    # Convert the dictionary to a YAML string
    yaml_data = yaml.dump(project_dict, default_flow_style=False)

    # Write the YAML data to a file
    with open(filename, "w") as file:
        file.write(yaml_data)
