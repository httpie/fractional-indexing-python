install:
	poetry --version || python3 -m pip install poetry
	poetry install

test:
	poetry run pytest tests.py --verbose

release:
	rm -rf build dist
	python setup.py sdist bdist_wheel
	twine upload --repository=fractional-indexing dist/*
