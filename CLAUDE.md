# CLAUDE.md — devops-demo

## Qué es este proyecto

Proyecto de portafolio DevOps que automatiza el ciclo de vida completo de una aplicación web mínima (Flask): build, test, empaquetado en Docker, push a un registro de imágenes (ECR), simulación de permisos AWS (IAM), despliegue y verificación — todo corriendo localmente sin necesitar una cuenta de AWS real.

El foco no es la aplicación en sí (que es deliberadamente simple), sino la infraestructura de CI/CD que la rodea.

## Estructura del proyecto

```
devops-demo/
├── app/
│   ├── app.py            # Flask app — dos endpoints: / y /health
│   ├── Dockerfile        # Multi-stage: stage test + stage production
│   ├── .dockerignore     # Excluye __pycache__, .env, *.md del contexto
│   ├── requirements.txt  # flask, gunicorn, pytest — todos pinneados
│   └── test_app.py       # 6 tests: status, estructura JSON, ENV override
├── docker-compose.yml    # Jenkins (8090) + LocalStack (4566)
├── Jenkinsfile           # Pipeline de 9 stages
├── .env                  # LOCALSTACK_AUTH_TOKEN — no commiteado
└── .gitignore            # .env, __pycache__, .vs/, IDEs, OS artifacts
```

## Decisiones de diseño importantes

### Multi-stage Dockerfile
El Dockerfile tiene dos stages: `test` y `production`.
- `docker build --target test` corre pytest dentro del build — si un test falla, el build falla
- `docker build --target production` produce la imagen limpia: solo `app.py` y `requirements.txt`, usuario no-root (appuser UID 1001), gunicorn como servidor

La imagen de producción no contiene test_app.py porque el stage production solo hace `COPY app.py .`.

### Docker socket mount (no DinD)
Jenkins corre dentro de un contenedor pero necesita construir y correr contenedores Docker. La solución es montar el socket del Docker daemon del host (`/var/run/docker.sock`) en el contenedor de Jenkins. Esto le da a Jenkins acceso al Docker daemon real del host, evitando Docker-in-Docker (DinD) que tiene problemas de performance y seguridad.

Implicación: cuando el pipeline hace `docker run` o `docker build`, esos contenedores son hermanos del contenedor Jenkins, no hijos. Por eso la red `devops-demo_default` es accesible desde esos contenedores — todos están en el mismo Docker daemon.

### LocalStack para AWS
LocalStack simula ECR, S3 e IAM localmente. Las llamadas usan `--endpoint-url=http://localstack:4566` dentro de la red Docker, y `localhost:4566` desde el host. Las credenciales son siempre `test/test`.

Para que el push a ECR funcione, Docker Desktop necesita tener `localhost:4566` en `insecure-registries`.

### Red Docker en el pipeline
Los contenedores que corren aws-cli y curlimages/curl en el pipeline se conectan a `devops-demo_default` (la red que crea docker-compose) para poder resolver `localstack` y `devops-demo-app` por nombre.

### Orden del pipeline
Test va ANTES de Build Image. Si los tests fallan, no se construye la imagen de producción ni se toca ECR. Fail fast.

## Cómo probar localmente

```bash
# Tests unitarios (sin Docker)
cd app
pip install -r requirements.txt
pytest test_app.py -v

# Build del stage de test (corre pytest dentro del build)
docker build --target test -t devops-demo:test ./app

# Build de producción
docker build --target production -t devops-demo:prod ./app

# Correr la app
docker run -p 5000:5000 -e ENV=production devops-demo:prod

# Verificar endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
```

## Cómo levantar el entorno completo

```bash
# 1. Crear .env con el token de LocalStack
echo "LOCALSTACK_AUTH_TOKEN=tu_token" > .env

# 2. Levantar Jenkins y LocalStack
docker compose up -d

# 3. Obtener contraseña inicial de Jenkins
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 4. Abrir http://localhost:8090, instalar plugin "Docker Pipeline"
# 5. Crear pipeline job apuntando a este repo
```

## Mejoras pendientes identificadas

- pytest sigue instalado en la imagen de producción (debería ir a requirements-dev.txt)
- Sin HEALTHCHECK en el Dockerfile ni en docker-compose
- Versiones no fijadas en docker-compose (jenkins:lts, localstack/localstack sin tag)
- Gunicorn arranca con 1 worker (sin --workers flag)
- Sin cleanup de imágenes viejas en el pipeline
- IMAGE_TAG usa prefijo "1." hardcodeado en lugar de semver limpio

## Tecnologías y versiones

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.12 | Runtime de la app |
| Flask | 3.0.3 | Framework web |
| Gunicorn | 22.0.0 | Servidor WSGI de producción |
| pytest | 8.3.2 | Framework de tests |
| Docker | 27+ | Containerización |
| Jenkins | LTS | Motor CI/CD |
| LocalStack | latest | Simulación de AWS (ECR, S3, IAM) |
