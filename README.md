# Prediagnóstico empresarial (Flask)

Aplicación web en Flask con un cuestionario de 25 preguntas para un prediagnóstico rápido de gestión empresarial.

## Ejecutar

1) Crear y activar entorno virtual (opcional pero recomendado).

```bash
python -m venv .venv
source .venv/bin/activate
```

2) Instalar dependencias.

```bash
pip install -r requirements.txt
```

3) Iniciar servidor.

```bash
flask --app app run --debug
```

Abrir `http://127.0.0.1:5000`.

## Docker

Build y ejecución:

```bash
docker compose up --build
```

Abrir `http://127.0.0.1:5000`.

Ejecución sin compose:

```bash
docker build -t pfiscalformulario .
docker run --env-file .env -p 5000:5000 pfiscalformulario
```

Notas:

- `docker-compose.yml` carga variables desde `.env` (por ejemplo `OPENAI_API_KEY`).
- El compose monta el proyecto como volumen para desarrollo.
- El contenedor (sin compose) usa `gunicorn` por defecto (ver `Dockerfile`).
- Para producción, define `SECRET_KEY` en `.env`.

## Estilos (Tailwind v4)

- La app carga únicamente `static/output.css` (ver `templates/base.html`).
- Genera ese archivo con tu build de Tailwind v4 (según tu entorno).

## Diagnóstico de venta con OpenAI (opcional)

Si defines `OPENAI_API_KEY`, la vista de resultados intentará generar un mensaje comercial basado en el scoring: identifica el problema principal, describe el dolor y explica cómo PlanetaFiscal puede ayudar.

Ejemplo de .env

Variables:

- `OPENAI_API_KEY`: tu API key (requerida para activar la IA)
- `OPENAI_MODEL`: modelo a usar (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL`: base URL (default: `https://api.openai.com/v1`)
- `OPENAI_TIMEOUT_SECONDS`: timeout (default: `10`)
- `OPENAI_API_MODE`: `auto` (default), `responses` o `chat_completions` (útil si tu `OPENAI_BASE_URL` no soporta `/responses` o si usas un proxy compatible)

Ejemplo:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_API_MODE="auto"
flask --app app run --debug
```

## Notas

- El resultado se calcula en el servidor y se guarda temporalmente en sesión (no hay base de datos).
- Para producción, cambia `SECRET_KEY` (ver `app.py`).
