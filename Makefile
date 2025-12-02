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

generate-key:
	python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

create-env:
	@if [ -f .env ]; then \
		echo ".env already exists"; \
	else \
		echo "Creating .env file..."; \
		echo 'PROJECT_NAME="AI Visibility Platform"' > .env; \
		echo 'MAX_CONCURRENT_REQUESTS=5' >> .env; \
		echo 'REQUEST_TIMEOUT_SECONDS=30' >> .env; \
		echo 'RATE_LIMIT_DELAY_SECONDS=0.1' >> .env; \
		echo '' >> .env; \
		echo '# Choose Provider: mock, openai, gemini, anthropic, or auto' >> .env; \
		echo 'LLM_PROVIDER=mock' >> .env; \
		echo '' >> .env; \
		echo '# Security' >> .env; \
		KEY=$$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"); \
		echo "ENCRYPTION_KEY=$$KEY" >> .env; \
		echo '' >> .env; \
		echo '# OpenAI Configuration' >> .env; \
		echo 'OPENAI_API_KEY=' >> .env; \
		echo '' >> .env; \
		echo '# Google Gemini Configuration' >> .env; \
		echo 'GEMINI_API_KEY=' >> .env; \
		echo '' >> .env; \
		echo '# Anthropic Configuration' >> .env; \
		echo 'ANTHROPIC_API_KEY=' >> .env; \
		echo ".env created successfully"; \
	fi

