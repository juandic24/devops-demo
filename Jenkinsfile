pipeline {
    agent any

    environment {
        IMAGE_NAME   = "devops-demo"
        IMAGE_TAG    = "1.${BUILD_NUMBER}"
        ECR_REGISTRY = "localhost:4566"
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
                echo "Ejecutando tests (falla el build si pytest falla)..."
                sh "docker build --target test -t ${IMAGE_NAME}:test-${IMAGE_TAG} ./app"
            }
        }

        stage('Build Image') {
            steps {
                echo "Construyendo imagen de produccion..."
                sh "docker build --target production -t ${IMAGE_NAME}:${IMAGE_TAG} ./app"
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
                    POLICY='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
                    docker run --rm \
                        --network devops-demo_default \
                        -e AWS_ACCESS_KEY_ID=test \
                        -e AWS_SECRET_ACCESS_KEY=test \
                        -e AWS_DEFAULT_REGION=us-east-1 \
                        amazon/aws-cli \
                        --endpoint-url=http://localstack:4566 \
                        iam create-role \
                        --role-name devops-demo-deploy-role \
                        --assume-role-policy-document "$POLICY" \
                        2>/dev/null || echo "Rol ya existe"
                '''
            }
        }

        stage('ECR - Push imagen') {
            steps {
                echo "Autenticando y haciendo push a ECR (LocalStack)..."
                sh '''
                    ECR_PASS=$(docker run --rm \
                        --network devops-demo_default \
                        -e AWS_ACCESS_KEY_ID=test \
                        -e AWS_SECRET_ACCESS_KEY=test \
                        -e AWS_DEFAULT_REGION=us-east-1 \
                        amazon/aws-cli \
                        --endpoint-url=http://localstack:4566 \
                        ecr get-login-password --region us-east-1)

                    echo "$ECR_PASS" | docker login \
                        --username AWS \
                        --password-stdin localhost:4566

                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} localhost:4566/${IMAGE_NAME}:${IMAGE_TAG}
                    docker tag ${IMAGE_NAME}:latest       localhost:4566/${IMAGE_NAME}:latest

                    docker push localhost:4566/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push localhost:4566/${IMAGE_NAME}:latest
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
                        --network devops-demo_default \
                        -p 5000:5000 \
                        -e ENV=production \
                        ${IMAGE_NAME}:latest
                '''
                sh "docker ps --filter name=devops-demo-app"
            }
        }

        stage('Smoke Test') {
            steps {
                echo "Verificando que la app responde..."
                sh '''
                    docker run --rm \
                        --network devops-demo_default \
                        curlimages/curl \
                        --retry 5 --retry-delay 2 --retry-connrefused \
                        -sf http://devops-demo-app:5000/health
                '''
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
