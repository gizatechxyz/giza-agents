from functools import wraps
import json
import os
from typing import Callable

from prefect import task as prefect_task
from prefect import Flow
from prefect import flow as _flow
from prefect.flows import load_flow_from_entrypoint
from prefect_gcp import GcpCredentials, CloudRunJob, GcsBucket


class Action():
    def __init__(self, flow: Flow, name: str):
        self.name = name
        self._flow = flow
        self.gcp_credentials = self._set_credentials()
        self._init_infrastrucure()

    def _init_infrastrucure(self):
        # Initialize infrastructure for the platform

        # must be from GCR and have Python + Prefect
        image = f"us-docker.pkg.dev/{os.environ['GCP_PROJECT_ID']}/test-example-repository/prefect-gcp:2-python3.11"  # noqa

        cloud_run_job = CloudRunJob(
            image=image,
            credentials=self.gcp_credentials,
            region=os.environ["CLOUD_RUN_JOB_REGION"],
        )
        cloud_run_job.save(os.environ["CLOUD_RUN_JOB_BLOCK_NAME"], overwrite=True)

        bucket_name = "prefect-actions-bucket"
        # cloud_storage_client = self.gcp_credentials.get_cloud_storage_client()
        # cloud_storage_client.create_bucket(bucket_name)
        gcs_bucket = GcsBucket(
            bucket=bucket_name,
            gcp_credentials=self.gcp_credentials,
        )
        gcs_bucket.save(os.environ["GCS_BUCKET_BLOCK_NAME"], overwrite=True)

        
    def _set_credentials(self):
        # Set credentials for the platform
        return GcpCredentials(service_account_file="../../credentials.json")
        
    def get_flow(self):
        return self._flow

    def serve(self, name: str):
        # Deploy the flow to the platform
        self._flow.serve(name=name,)
    
    def execute(self):
        # Implement the execution logic here
        # load_flow_from_entrypoint(self._flow)
        self._flow()

    def apply(self, inference_id: int):
        # Implement the apply logic here
        pass


def action(*args, **kwargs) -> Callable:
    def decorator(function):
        @_flow(name=function.__name__, *args, **kwargs)
        @wraps(function)
        def _inner(*args, **kwargs):
            return function(*args, **kwargs)
        action_instance = Action(flow=_inner, name=function.__name__)
        return action_instance.get_flow()
    return decorator
