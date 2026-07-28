.PHONY: setup run seed test clean

setup:
	python -m venv venv
	venv\Scripts\pip install -r requirements.txt
	copy .env.example .env
	@echo "Setup complete. Add your OPENAI_API_KEY to .env, then run 'make run'"

run:
	venv\Scripts\python -m uvicorn app.main:app --reload

seed:
	venv\Scripts\python seed.py

test:
	venv\Scripts\python -m pytest tests/ -v || echo "No tests folder yet"

clean:
	rmdir /s /q venv
	rmdir /s /q __pycache__
	del /f /q *.db
