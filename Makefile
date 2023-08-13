install:
	poetry --version || python3 -m pip install poetry
	poetry install

test:
	poetry run pytest tests.py --verbose

clean:
	rm -rf build dist
release: clean
	poetry run python setup.py sdist bdist_wheel
	poetry run twine upload --repository=fractional-indexing dist/*
