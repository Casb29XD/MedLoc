# MedLoc

## Ejecutar backend y frontend con Docker

Desde la raíz del repositorio:

```bash
docker compose up --build
```

Esto inicia el backend Flask en `http://localhost:5000` y el frontend Vite
en `http://localhost:5173`. Las peticiones del frontend a `/api` se envían
al servicio `backend` dentro de la red de Docker, por lo que no dependen de
`localhost` dentro del contenedor.

Para probar la compilación de producción con nginx:

```bash
docker compose --profile prod up --build frontend-prod
```

La versión de producción queda disponible en `http://localhost:8080` y nginx
redirige internamente `/api` al backend.