pipeline {
    agent any

    environment {
        IMAGE_NAME = "devops-demo"
        IMAGE_TAG  = "1.${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Clonando repositorio..."
                checkout scm
            }
        }

        stage('Test') {
            steps {
                echo "Ejecutando tests..."
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
            }
        }

        stage('Push to ECR (LocalStack)') {
            steps {
                echo "Haciendo push a ECR local..."
                sh '''
                    aws --endpoint-url=http://localstack:4566 ecr create-repository \
                        --repository-name devops-demo --region us-east-1 2>/dev/null || true

                    docker tag devops-demo:latest \
                        localhost:4566/devops-demo:latest

                    docker push localhost:4566/devops-demo:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo "Desplegando contenedor..."
                sh '''
                    docker stop devops-demo-app 2>/dev/null || true
                    docker rm devops-demo-app 2>/dev/null || true
                    docker run -d \
                        --name devops-demo-app \
                        -p 5000:5000 \
                        -e ENV=production \
                        devops-demo:latest
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline exitoso. App corriendo en puerto 5000."
        }
        failure {
            echo "Pipeline fallido. Revisar logs."
        }
    }
}
