# OES Webhooks

A collection of useful webhooks.

## Development Setup

- Install the development environment with [Poetry](https://python-poetry.org/):

      poetry install

- Install [pre-commit](https://pre-commit.com/) and run:

      pre-commit install

  to configure the linting/formatting hooks.

- Run tests with `poetry run pytest`.

## Configuration

- Copy `config.example.yml` to `config.yml` and edit the settings appropriately.

## Running

Run the server with `oes-webooks -c config.yml`.
