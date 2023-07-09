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

Copy `config.example.yml` to `config.yml` and edit the settings appropriately.

Configuration settings can be overridden via environment variables, like
`OES_WEBHOOKS_EMAIL_USE=mock`.

## Running

Run the server with `oes-webhooks -c config.yml`.

**Warning:** This software is meant to run inside a private network and must not be
accessible to the public internet.

## Endpoints

#### `POST /email/<path>`

Send an email. Accepts the following properties:

`to`
: The recipient. May be formatted like `User Name <email@site.com>`.

`from` (optional)
: The sender. May be formatted like `User Name <email@site.com>`.

`subject` (optional)
: The message subject.

Any additional properties will be made available to the template rendering the email.

The `path` parameter will be used to look up the template within the `template_path` in
the configuration.

##### Templates

Email templates are rendered using [Jinja](https://palletsprojects.com/p/jinja/). For a
request with a given `path`, the system will look for a file at
`<template_path>/<path>.txt` and render it to create a plain-text version of the
message. It will also look for an optional file at `<template_path>/<path>.html`, which
if found, will be used to render the HTML version of the message.

The HTML versions will have all CSS styles inlined and the resulting HTML will be
minified.

##### Attachments

Within a template, the `inline` and `attach` functions can be used to attach a file as
inline content or an attachment, respectively. The function returns the `Content-ID`
value which can be referenced to embed images.

Example:

```
{% set content_id = inline("logo.png") %}
<img src="cid:{{ content_id }}" alt="Logo" />
```

##### Overriding the Subject

A template can override the message subject using the `set_subject()` or
`default_subject()` functions.

`set_subject()` will unconditionally set the subject of the message, while
`default_subject()` will only set it if a subject was not already set. Both functions
return the resulting subject.

Example:

```
<h1>{{ set_subject("Verify Your Email") }}</h1>
```
