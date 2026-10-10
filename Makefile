.PHONY: setup backend frontend

setup:
	bash setup-local.sh

backend:
	set -a; [ ! -f .env ] || . ./.env; set +a; python3 -m uvicorn backend.app.main:app --reload --port 8000

frontend:
	npm run dev
