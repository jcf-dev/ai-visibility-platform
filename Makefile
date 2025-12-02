install:
	pip install -r requirements.txt
	cd frontend && npm install

run:
	uvicorn app.main:app --reload

run-frontend:
	cd frontend && npm run dev

run-all:
	make -j 2 run run-frontend

test:
	PYTHONPATH=. pytest

run-sample:
	python scripts/run_sample.py

format:
	black .

lint:
	flake8 .

