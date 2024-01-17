format:
	pipenv run isort --diff .
	pipenv run black --check .
	pipenv run flake8
	pipenv run mypy

coverage:
	pipenv run pytest --cov --cov-fail-under=100