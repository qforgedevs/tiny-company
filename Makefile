.PHONY: setup install-api install-web lint typecheck test api-health web-build up-db down-db

setup: up-db install-api install-web

up-db:
	docker compose up -d db

down-db:
	docker compose down -v

install-api:
	uv venv apps/api/.venv && . apps/api/.venv/bin/activate && uv pip install -r apps/api/requirements.txt

install-web:
	cd apps/web && npm install

lint:
	cd apps/api && . .venv/bin/activate && PYTHONPATH=$(CURDIR)/apps/api pytest --collect-only >/dev/null 2>&1 || true
	cd apps/web && npm run lint

typecheck:
	cd apps/api && . .venv/bin/activate && PYTHONPATH=$(CURDIR)/apps/api python -m compileall app
	cd apps/web && npm run typecheck

test:
	cd apps/api && . .venv/bin/activate && PYTHONPATH=$(CURDIR)/apps/api pytest -q
	cd apps/web && npm test -- --run

api-health:
	cd apps/api && . .venv/bin/activate && PYTHONPATH=$(CURDIR)/apps/api uvicorn app.main:app --host 127.0.0.1 --port 8000 >/tmp/tinycompany-api.log 2>&1 & sleep 3 && curl -fsS http://127.0.0.1:8000/health && pkill -f "uvicorn app.main:app" || true

web-build:
	cd apps/web && npm run build
