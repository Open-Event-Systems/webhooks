FROM python:3.10.12-alpine3.18 AS python

FROM python AS build
RUN apk add git build-base rust cargo
WORKDIR /build
RUN pip install --no-cache-dir poetry wheel
RUN python -m venv /app
COPY pyproject.toml poetry.lock ./
RUN poetry export | grep -v '^oes-' > requirements.txt
RUN pip wheel --no-cache-dir -w deps -r requirements.txt
RUN /app/bin/pip install --no-cache-dir deps/*
COPY README.md ./
COPY src/ src/
RUN /app/bin/pip install --no-cache-dir .

FROM python AS webhooks
RUN apk add libgcc
RUN adduser -h /app -H -D python \
    && mkdir /config
COPY --chown=python:python config.example.yml /config/config.yml
COPY --chown=python:python templates/ /config/templates/
COPY --from=build /app/ /app/
WORKDIR /app
USER python
ENV PATH=$PATH:/app/bin
EXPOSE 8002
ENTRYPOINT ["/app/bin/oes-webhooks"]
CMD ["--config", "/config/config.yml", "--bind", "0.0.0.0"]
