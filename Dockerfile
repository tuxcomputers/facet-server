FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /workspace

RUN apt-get update && apt-get install --yes --no-install-recommends bash git postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash dev \
    && echo 'dev ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers \
    && echo "alias ll='ls -lhF --color=auto --group-directories-first'" >> /home/dev/.bashrc

# Dependencies come from pyproject.toml and nowhere else, so there is one list to keep
# current. The package itself is bind-mounted over /workspace at run time; this install is
# for its dependencies. Adding a dependency means rebuilding: docker compose build server.
COPY pyproject.toml ./
COPY facet_server ./facet_server
RUN pip install --no-cache-dir ".[dev]"

CMD ["alembic", "upgrade", "head"]
