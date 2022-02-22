install:
	poetry --version || python3 -m pip install poetry
	poetry install

test:
	poetry run pytest tests.py --verbose
