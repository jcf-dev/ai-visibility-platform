install:
	pip install -r requirements.txt
	cd frontend && npm install

run-backend-dev:
	uvicorn app.main:app --reload

run-frontend-dev:
	cd frontend && npm run dev

run-dev:
	make -j 2 run-backend-dev run-frontend-dev

build-frontend:
	cd frontend && npm run build

run-backend-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

run-frontend-prod:
	cd frontend && npm run start

run-prod: build-frontend
	make -j 2 run-backend-prod run-frontend-prod

test:
	PYTHONPATH=. pytest

run-sample:
	python scripts/run_sample.py

format:
	black .

lint:
	flake8 .

