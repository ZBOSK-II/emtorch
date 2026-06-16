# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

#
# poetry builder
#
FROM python:3.14-slim-bookworm AS poetry-builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    git=1:2.39.* \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=2.4.1
ENV POETRY_VENV=/opt/poetry-venv

RUN python3 -m venv ${POETRY_VENV} \
    && ${POETRY_VENV}/bin/pip install -U pip setuptools \
    && ${POETRY_VENV}/bin/pip install poetry==${POETRY_VERSION}

ENV POETRY=${POETRY_VENV}/bin/poetry

WORKDIR /emtorch

COPY . /emtorch
RUN ${POETRY} install --no-interaction --no-root
RUN ${POETRY} build --no-interaction
# export frozen requirements
RUN ${POETRY} export --no-interaction > dist/requirements.txt

#
# installation base
#
FROM python:3.14-slim-bookworm AS install-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# apps
RUN apt-get update -q \
    && DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends \
    iputils-ping=3:* \
    openssh-client=1:9.2* \
    && rm -rf /var/lib/apt/lists/*

#
# development image
#
FROM install-base AS emtorch-dev

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV POETRY_VENV=/opt/poetry-venv
COPY --from=poetry-builder ${POETRY_VENV}/ /opt/poetry-venv/
ENV POETRY=${POETRY_VENV}/bin/poetry

ENV PATH="${POETRY_VENV}/bin:$PATH"

ADD pyproject.toml .
RUN ${POETRY} install --no-root --no-interaction --with=dev

#
# final image
#
FROM install-base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV EMTORCH_VENV=/opt/emtorch-venv

RUN python -m venv ${EMTORCH_VENV}

# emtorch from poetry
WORKDIR /emtorch
COPY --from=poetry-builder /emtorch/dist /emtorch
RUN ${EMTORCH_VENV}/bin/pip install -r requirements.txt \
  && ${EMTORCH_VENV}/bin/pip install emtorch*.whl \
  && ln -sr ${EMTORCH_VENV}/bin/emtorch /usr/bin

CMD ["emtorch"]
