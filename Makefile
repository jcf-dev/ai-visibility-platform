install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	PYTHONPATH=. pytest

run-sample:
	python scripts/run_sample.py

format:
	black .

lint:
	flake8 .

