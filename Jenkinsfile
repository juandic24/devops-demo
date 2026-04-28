pipeline {
    agent any

    environment {
        IMAGE_NAME = "devops-demo"
        IMAGE_TAG  = "1.${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Clonando repositorio desde GitHub..."
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "Ejecutando tests dentro de contenedor Python..."
                sh '''
                    docker run --rm \
                        -v $(pwd)/app:/app \
                        -w /app \
                        python:3.12-slim \
                        sh -c "pip install -q -r requirements.txt && python -m pytest test_app.py -v"
                '''
            }
        }

        stage('Build Image') {
            steps {
                echo "Construyendo imagen Docker..."
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ./app"
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
                sh "docker images ${IMAGE_NAME}"
            }
        }

        stage('ECR - Crear repositorio') {
            steps {
                echo "Creando repositorio en ECR (LocalStack)..."
                sh '''
                    docker run --rm \
                        --network devops-demo_default \
                        -e AWS_ACCESS_KEY_ID=test \
                        -e AWS_SECRET_ACCESS_KEY=test \
                        -e AWS_DEFAULT_REGION=us-east-1 \
                        amazon/aws-cli \
                        --endpoint-url=http://localstack:4566 \
                        ecr create-repository \
                        --repository-name devops-demo \
                        --region us-east-1 2>/dev/null || echo "Repositorio ya existe"
                '''
            }
        }

        stage('ECR - Listar repositorios') {
            steps {
                echo "Verificando repositorios en ECR (LocalStack)..."
                sh '''
                    docker run --rm \
                        --network devops-demo_default \
                        -e AWS_ACCESS_KEY_ID=test \
                        -e AWS_SECRET_ACCESS_KEY=test \
                        -e AWS_DEFAULT_REGION=us-east-1 \
                        amazon/aws-cli \
                        --endpoint-url=http://localstack:4566 \
                        ecr describe-repositories \
                        --region us-east-1
                '''
            }
        }

        stage('IAM - Simular rol de deploy') {
            steps {
                echo "Creando rol IAM para deploy (LocalStack)..."
                sh '''
                    docker run --rm \
                        --network devops-demo_default \
                        -e AWS_ACCESS_KEY_ID=test \
                        -e AWS_SECRET_ACCESS_KEY=test \
                        -e AWS_DEFAULT_REGION=us-east-1 \
                        amazon/aws-cli \
                        --endpoint-url=http://localstack:4566 \
                        iam create-role \
                        --role-name devops-demo-deploy-role \
                        --assume-role-policy-document '"'"'{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'"'"' \
                        2>/dev/null || echo "Rol ya existe"
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Desplegando contenedor (simula deploy en EC2)..."
                sh '''
                    docker stop devops-demo-app 2>/dev/null || true
                    docker rm   devops-demo-app 2>/dev/null || true
                    docker run -d \
                        --name devops-demo-app \
                        -p 5000:5000 \
                        -e ENV=production \
                        devops-demo:latest
                '''
                sh "docker ps --filter name=devops-demo-app"
            }
        }

        stage('Smoke Test') {
            steps {
                echo "Verificando que la app responde..."
                sh "sleep 3 && curl -sf http://host.docker.internal:5000/health"
            }
        }
    }

    post {
        success {
            echo "Pipeline exitoso. App corriendo en http://localhost:5000"
        }
        failure {
            echo "Pipeline fallido. Revisar logs de cada stage."
            sh "docker logs devops-demo-app 2>/dev/null || true"
        }
    }
}
