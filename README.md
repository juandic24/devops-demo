# DevOps Demo

A DevOps demonstration project showcasing a complete CI/CD workflow using Flask, Docker, Jenkins, and LocalStack (AWS simulation) — all running locally without requiring real AWS infrastructure.

## Overview

This project builds a minimal Flask REST API and automates its entire lifecycle: build, test, container registry push (ECR), IAM role simulation, deployment, and smoke testing — driven by a Jenkins pipeline running inside Docker Compose.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│   ┌─────────────┐          ┌──────────────────────┐    │
│   │   Jenkins   │─────────▶│     LocalStack       │    │
│   │  (CI/CD)    │          │  ECR · S3 · IAM      │    │
│   └──────┬──────┘          └──────────────────────┘    │
│          │ builds & deploys                             │
│   ┌──────▼──────┐                                       │
│   │  Flask App  │  :5000                                │
│   │  Container  │                                       │
│   └─────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Application | Python 3.12, Flask 3.0 |
| Containerization | Docker (python:3.12-slim) |
| CI/CD | Jenkins LTS |
| AWS Simulation | LocalStack (ECR, S3, IAM) |
| Testing | pytest 8.3 |
| Orchestration | Docker Compose |

## Project Structure

```
devops-demo/
├── app/
│   ├── app.py            # Flask application
│   ├── Dockerfile        # Container image definition
│   ├── requirements.txt  # Python dependencies
│   └── test_app.py       # pytest unit tests
├── docker-compose.yml    # Jenkins + LocalStack environment
├── Jenkinsfile           # CI/CD pipeline definition
└── .env                  # LocalStack auth token (not committed)
```

## Application Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Returns app name and version |
| GET | `/health` | Returns health status and current environment |

Example responses:

```json
// GET /
{ "app": "DevOps Demo App", "version": "1.0" }

// GET /health
{ "status": "healthy", "env": "production" }
```

## CI/CD Pipeline Stages

The `Jenkinsfile` defines 9 automated stages:

1. **Checkout** — Pull source code from SCM
2. **Build Image** — Build Docker image tagged as `devops-demo:1.<BUILD_NUMBER>` and `latest`
3. **Test** — Run pytest inside the container
4. **ECR - Create Repository** — Create ECR repository in LocalStack
5. **ECR - List Repositories** — Verify repository creation
6. **IAM - Simulate Deploy Role** — Create IAM deploy role in LocalStack
7. **Deploy** — Replace running container with the new image
8. **Smoke Test** — Hit `/health` endpoint to verify the deployment
9. **Post Actions** — Print logs on failure; report success

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker socket exposed)
- [Docker Compose](https://docs.docker.com/compose/) v2+
- A LocalStack Auth Token (free tier works) — set it in `.env`

## Getting Started

### 1. Configure environment

Create a `.env` file in the project root:

```env
LOCALSTACK_AUTH_TOKEN=your_token_here
```

### 2. Start the environment

```bash
docker compose up -d
```

This starts Jenkins on `http://localhost:8090` and LocalStack on `http://localhost:4566`.

### 3. Configure Jenkins

On first run, retrieve the initial admin password:

```bash
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Then open `http://localhost:8090`, complete the setup wizard, and install the **Docker Pipeline** plugin.

### 4. Create a pipeline job

1. New Item → Pipeline
2. Set **Definition** to *Pipeline script from SCM*
3. Point SCM to this repository
4. Save and click **Build Now**

## Running Tests Locally

```bash
cd app
pip install -r requirements.txt
pytest test_app.py -v
```

## Running the App Locally

```bash
cd app
pip install -r requirements.txt
python app.py
# App available at http://localhost:5000
```

Or with Docker:

```bash
docker build -t devops-demo ./app
docker run -p 5000:5000 devops-demo
```

## Notes

- **LocalStack** replaces real AWS services (ECR, S3, IAM) for local development and CI simulation. No AWS account is needed.
- The Jenkins container mounts the host Docker socket (`/var/run/docker.sock`) to build and run containers from within the pipeline (Docker-in-Docker pattern).
- Image versions follow the scheme `1.<BUILD_NUMBER>` and are also tagged as `latest`.
