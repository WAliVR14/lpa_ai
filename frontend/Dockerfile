# ==============================================================================
# Dockerfile Frontend - Single Page Application React + Vite (Multi-Stage)
# ==============================================================================

# --- Etapa 1: Construcción (Build) ---
FROM node:20-alpine AS build

WORKDIR /app

# Copiar manifiestos primero para cachear la instalación de dependencias
COPY package.json package-lock.json* ./

RUN npm install

# Copiar el código fuente y compilar estáticos de producción
COPY . .

RUN npm run build

# --- Etapa 2: Servidor Web de Producción (Nginx) ---
FROM nginx:alpine

# Limpiar archivos por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar los artefactos compilados desde la etapa de build
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración de Nginx con soporte para SPA y proxy reverso
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

