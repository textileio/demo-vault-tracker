# Vaults Tracker

[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg)](https://github.com/RichardLitt/standard-readme)

> Fetch & inspect the latest Basin vaults.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
  - [Running the script](#running-the-script)
  - [Makefile reference](#makefile-reference)
- [Contributing](#contributing)

## Background

This project is a simple tool to track the new vaults that are created with [Basin](https://github.com/tablelandnetwork/basin-cli).

The script fetches data from onchain events at the Basin [storage contract](https://github.com/tablelandnetwork/basin-storage/blob/main/evm/basin_storage/src/BasinStorage.sol) on Filecoin Calibration (`0xaB16d51Fa80EaeAF9668CE102a783237A045FC37`), retrieves relevant information from the Basin [HTTP API](https://github.com/tablelandnetwork/basin-provider/pull/17), and does this all on a weekly cron schedule with GitHub Actions. For every run, it will write the results to:

-   [Data](./Data.md): Summary data for all vaults ever created.
-   [State](./history.csv): A JSON file containing the full history of all runs, along with the relevant log/event data and cumulative vaults created.

## Install

For working on your machine, make sure `pipx` and `pipenv` are installed.

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

These latter steps are also available in the Makefile as `make install` and `make setup`. This project also uses python 3.12, so make sure you have that installed. You can see a full list of requirements in the [Pipfile](./Pipfile).

> Note: This project was created with Cookiecutter and the [sourcery-ai](https://github.com/sourcery-ai/python-best-practices-cookiecutter) project template—check it out!

## Usage

### Running the script

The `vaults_tracker` module is the main entrypoint for the project. You can run it with:

```sh
make run
```

This will fetch new events that have occurred after the latest run & block number in the [state](./state.json) file, and write the results to the [Data](./Data.md) file. The data file lists out each vault owner's address, the vault's name, and a link to the vault mutation "events" (CIDs) for subsequent retrieval. You can see the GitHub actions setup in the [workflow file](./.github/workflows/weekly.yml).

### Makefile reference

The following defines all commands available in the Makefile:

-   `make install`: Install dependencies with `pipenv`.
-   `make setup`: Install pre-commit and pre-push hooks that run checks on the code.
-   `make format`: Directly run `black`, `isort`, `flake8`, and `mypy` on the project.
-   `make coverage`: Not used but available if tests are written.

## Contributing

PRs accepted. Be sure to run the pre-commit and pre-push hooks, and the `make format` command also does similar actions.

Small note: If editing the README, please conform to the standard-readme specification.
