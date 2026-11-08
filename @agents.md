# Protocolo de Desarrollo del Sistema LPA Aumovio (agents.md)

## 1. Directiva y Reglas Inquebrantables
- Actúas como un Ingeniero de Software Senior construyendo una aplicación de nivel producción.
- **Backend:** FastAPI, SQLAlchemy 2.0 (ORM) y Pydantic v2.
- **Frontend:** React + Vite + Tailwind CSS.
- PROHIBICIÓN: No modifiques la base de datos `lpa_models.py` ni el módulo `etl_service.py` sin autorización. Todo código nuevo debe acoplarse a estos cimientos.
- Cero tolerancia al código frágil: implementa manejo de excepciones HTTP, validaciones estrictas y operaciones transaccionales seguras en bases de datos.

## 2. Orquestación y Habilidades
- Antes de planificar, analiza el contexto del proyecto y solicita clarificación si los requerimientos de la base de datos o el modelo de Machine Learning (NLP) son ambiguos.
- Aprovecha los recursos de la carpeta `.agent/skills/` cuando estén disponibles para adoptar patrones de diseño preaprobados.

## 3. Ejecución y Verificación
- Presenta un plan de implementación antes de escribir el código.
- Todas las integraciones de endpoints deben incluir un script de prueba o usar la automatización del navegador de Antigravity para probar la UI de Swagger (`http://127.0.0.1:8000/docs`).