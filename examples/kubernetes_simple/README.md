# Kubernetes Deployment Example

This guide will walk you through the process of creating a Docker image and deploying an Action using Kubernetes on Google Cloud Platform (GCP).

## Prerequisites

- Google Cloud SDK installed and authenticated
- Docker installed
- Prefect installed

## Steps

1. Authenticate with Google Cloud:
   ```
   gcloud auth login
   ```

2. Create a Docker repository in Artifact Registry:
   ```
   gcloud artifacts repositories create prefect-test --repository-format=docker --location=us-west2 --description="Docker repository for testing Prefect"
   ```

3. Build the Docker image and push it to the Artifact Registry:
   ```
   gcloud builds submit --region=us-west2 --tag us-west2-docker.pkg.dev/giza-platform/prefect-test/prefect-flow-test:v0 
   ```

4. Deploy the Action:
   ```
   python deployment.py
   ```

After following these steps, your Action should be successfully deployed on Kubernetes.
