# vaults_tracker

## Setup

You can choose to use Docker, or for working on your machine, make sure `pipx` and `pipenv` are installed.

```sh
brew install pipx
pipx install pipenv
```

Then, install dependencies:

```sh
pipenv install --dev
```

And set up pre-commit and pre-push hooks:

```sh
pipenv run pre-commit install -t pre-commit
pipenv run pre-commit install -t pre-push
```

## Credits

This package was created with Cookiecutter and the [sourcery-ai/python-best-practices-cookiecutter](https://github.com/sourcery-ai/python-best-practices-cookiecutter) project template.
