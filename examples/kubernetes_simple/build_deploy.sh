#!/bin/bash

# Authenticate with Google Cloud
gcloud auth login

# Build the Docker image and push it to the Artifact Registry
gcloud builds submit --region=us-west2 --tag us-west2-docker.pkg.dev/giza-platform/prefect-test/prefect-flow-test:v0 

# Deploy the Action
python deployment.py