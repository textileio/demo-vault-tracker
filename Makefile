format:
	pipenv run isort --diff .
	pipenv run black --check .
	pipenv run flake8
	pipenv run mypy

install:
	pipenv install --dev

setup:
	pipenv run pre-commit install -t pre-commit
	pipenv run pre-commit install -t pre-push

coverage:
	pipenv run pytest --cov --cov-fail-under=100

run:
	pipenv run python -m vaults_tracker.__main__ 