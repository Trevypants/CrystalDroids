# CrystalDroids

Makefile commands:

```bash
make setup # runs all setup
```

Deployment to Cloud run for both Backend and Frontend

## Backend

Backend is hosted on Cloud Run in a Python web application that connects to Google Gemini for GenerativeAI and Firestore for storing all conversations.

## Frontend

Frontend is hosted on Cloud Run in a Javascript application that communicates with the backend.

## Deploy

Deployment via Github Actions with all GCP credentials stored as repository secrets.
