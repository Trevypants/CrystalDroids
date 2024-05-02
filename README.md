# CrystalDroids

Makefile commands:

```bash
make setup # runs all setup
```

Deployment to Cloud run for both Backend and Frontend

## Backend

Backend is hosted on Cloud Run in a Python web application that connects to Google Gemini for GenerativeAI and Firestore for storing all conversations.

## Frontend

Frontend is hosted on Cloud Run in a Python ui application that communicates with the backend.

## Deploy

Deployment via Github Actions with all GCP credentials stored as repository secrets/variables. Upon push to main, the Github Actions will build all necessary components (database, artifact registry, dockerfiles, cloud run, etc) and deploy the application. See the github actions for more details on deployment.

Requirements:

1. A Google Cloud Platform project (stored as a repository secret in `GCP_PROJECT_ID`)
2. A service account with the following permissions (SA email stored as a repository secret in `GCP_SERVICE_ACCOUNT_EMAIL`):
    - Cloud Datastore Owner
    - Storage Admin
    - Artifact Registry Admin
    - Cloud Run Admin
    - Cloud Run Service Agent
    - Vertex AI Admin
    - Vertex AI User
3. The service account key in JSON format (stored as a repository secret in `GCP_SERVICE_ACCOUNT_KEY`)
4. The following repository variables set:
    - `GCP_REGION` (e.g. `europe-west4`)
    - `GCP_ARTIFACT_REGISTRY` (e.g. `my-artifact-registry`)
    - `GCP_BUCKET_SUFFIX` (e.g. `my-bucket-suffix`)
    - `GCP_FIRESTORE_DB` (e.g. `my-firestore-db`)
    - `GCP_BACKEND_APP` (e.g. `my-backend-app`)
    - `GCP_FRONTEND_APP` (e.g. `my-frontend-app`)
