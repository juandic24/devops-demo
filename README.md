# DevOps Demo

A DevOps demonstration project showcasing a complete CI/CD workflow using Flask, Docker, Jenkins, and LocalStack (AWS simulation) — all running locally without requiring real AWS infrastructure.

## Overview

This project builds a minimal Flask REST API and automates its entire lifecycle: build, test, container registry push (ECR), IAM role simulation, deployment, and smoke testing — driven by a Jenkins pipeline running inside Docker Compose.

The focus is not the application itself (deliberately minimal), but the CI/CD infrastructure surrounding it.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Docker Compose                         │
│                                                              │
│  ┌─────────────────┐   shared network   ┌────────────────┐  │
│  │    Jenkins      │───────────────────▶│   LocalStack   │  │
│  │  port 8090      │                    │   port 4566    │  │
│  │                 │                    │ ECR · S3 · IAM │  │
│  │  Reads          │                    │ (mocks AWS)    │  │
│  │  Jenkinsfile    │                    └────────────────┘  │
│  │  and runs the   │                                        │
│  │  pipeline       │                                        │
│  └────────┬────────┘                                        │
│           │ mounts host Docker socket                       │
│           │ build · push · deploy                           │
│  ┌────────▼────────┐                                        │
│  │ devops-demo-app │                                        │
│  │   port 5000     │                                        │
│  │ Flask + Gunicorn│                                        │
│  └─────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```

Jenkins does not use Docker-in-Docker. Instead, it mounts the host Docker socket (`/var/run/docker.sock`), giving it access to the real Docker daemon without the complexity or security issues of DinD. Containers created by the pipeline are siblings of the Jenkins container, not children.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Application | Python 3.12, Flask 3.0 | Minimal framework to keep focus on the pipeline |
| Production server | Gunicorn 22.0 | Flask's dev server is not production-safe |
| Containerization | Docker, python:3.12-slim | Portable, reproducible packaging |
| CI/CD | Jenkins LTS | Industry-standard pipeline engine |
| AWS Simulation | LocalStack (ECR, S3, IAM) | Replicates AWS locally — no account or cost needed |
| Testing | pytest 8.3 | Tests integrated into the pipeline via multi-stage Docker build |
| Orchestration | Docker Compose | Runs Jenkins and LocalStack on a shared network |

## Dockerfile: Multi-Stage Build

The `Dockerfile` has two stages with distinct responsibilities:

```
Stage "test"
  ├── Installs all dependencies
  ├── Copies all source files (including test_app.py)
  └── Runs pytest — if a test fails, the build fails here

Stage "production"
  ├── Installs runtime dependencies only
  ├── Copies app.py only
  ├── Creates a non-root user (appuser, UID 1001)
  └── Starts with Gunicorn
```

The production image contains no test files, no Dockerfile, and no development artifacts. `.dockerignore` additionally excludes `__pycache__`, `.env`, and Markdown files from the build context.

## Project Structure

```
devops-demo/
├── app/
│   ├── app.py            # Flask application — / and /health endpoints
│   ├── Dockerfile        # Multi-stage: test + production
│   ├── .dockerignore     # Excludes dev/test files from the build context
│   ├── requirements.txt  # Pinned dependencies: flask, gunicorn, pytest
│   └── test_app.py       # 6 tests: status codes, JSON structure, ENV override
├── docker-compose.yml    # Jenkins (8090) + LocalStack (4566)
├── Jenkinsfile           # 9-stage pipeline definition
└── .env                  # LocalStack auth token (not committed)
```

## Application Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Returns app name and version |
| GET | `/health` | Returns health status and current environment |

```json
// GET /
{ "message": "DevOps Demo App", "version": "1.0" }

// GET /health
{ "status": "healthy", "env": "production" }
```

## CI/CD Pipeline Stages

```
Checkout → Test → Build Image → ECR Create → ECR List → IAM Role → ECR Push → Deploy → Smoke Test
```

| Stage | What it does |
|---|---|
| **Checkout** | Pulls source code from SCM |
| **Test** | `docker build --target test` — pytest runs inside the build; failure stops the pipeline |
| **Build Image** | `docker build --target production` — clean image tagged as `1.<BUILD_NUMBER>` and `latest` |
| **ECR - Create Repository** | Creates the image repository in LocalStack (idempotent) |
| **ECR - List Repositories** | Verifies the repository was created |
| **IAM - Simulate Deploy Role** | Creates an IAM role in LocalStack simulating EC2 deploy permissions |
| **ECR - Push Image** | Authenticates with ECR and pushes the image to LocalStack |
| **Deploy** | Replaces the running container with the new image on the shared Docker network |
| **Smoke Test** | `curl` from a container on the internal network hits `/health` — failure stops the pipeline |

The smoke test runs via `curlimages/curl` on the `devops-demo_default` network, making it portable across Linux, macOS, and Windows (no dependency on `host.docker.internal`).

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker socket exposed)
- [Docker Compose](https://docs.docker.com/compose/) v2+
- A LocalStack Auth Token (free tier works) — [localstack.cloud](https://localstack.cloud)

### Docker insecure registry (required for ECR push)

The ECR push stage pushes to LocalStack at `localhost:4566`. Docker requires this registry to be explicitly allowed as insecure. In Docker Desktop go to **Settings → Docker Engine** and add:

```json
{
  "insecure-registries": ["localhost:4566"]
}
```

Apply and restart Docker Desktop.

## Getting Started

### 1. Configure environment

```bash
echo "LOCALSTACK_AUTH_TOKEN=your_token_here" > .env
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

Open `http://localhost:8090`, complete the setup wizard, and install the **Docker Pipeline** plugin.

### 4. Create a pipeline job

1. New Item → Pipeline
2. Set **Definition** to *Pipeline script from SCM*
3. Point SCM to this repository
4. Save and click **Build Now**

## Local Development

**Run tests without Docker:**

```bash
cd app
pip install -r requirements.txt
pytest test_app.py -v
```

**Build and run only the test stage:**

```bash
docker build --target test -t devops-demo:test ./app
```

**Build and run the production image:**

```bash
docker build --target production -t devops-demo:prod ./app
docker run -p 5000:5000 -e ENV=production devops-demo:prod
```
