FROM python:3.10-buster AS builder

ARG PYPI_DEPLOY_TOKEN

ADD . /app

WORKDIR /app

ENV PIPENV_VENV_IN_PROJECT=1

RUN python -m venv --copies .venv && . .venv/bin/activate && pip install pipenv && pipenv sync

FROM python:3.10-slim-buster

COPY --from=builder /app /app

WORKDIR /app

ENV PIPENV_VENV_IN_PROJECT=1
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/near:${PYTHONPATH}"

# TODO: Switch to run prod when ready
ENTRYPOINT ["pipenv", "run"]
CMD ["dev"]
