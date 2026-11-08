.PHONY: help up down restart logs test build clean

help:
	@echo "Comandos disponibles para LPA AI Aumovio:"
	@echo "  make up       - Construye e inicia los contenedores en segundo plano"
	@echo "  make down     - Detiene y elimina los contenedores y redes"
	@echo "  make restart  - Reinicia los contenedores"
	@echo "  make logs     - Visualiza los logs en tiempo real de todos los servicios"
	@echo "  make test     - Ejecuta la suite de pruebas automatizadas en backend"
	@echo "  make build    - Reconstruye las imágenes de Docker"
	@echo "  make clean    - Limpia archivos temporales y cachés"

up:
	docker compose up --build -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

test:
	pytest backend/tests/ -v

build:
	docker compose build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache frontend/dist

