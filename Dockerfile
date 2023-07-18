FROM python:3.10-bullseye as builder

run apt-get update && apt-get install -y \
    build-essential

COPY requirements.txt .
RUN pip install --root="/install" -r requirements.txt


# runtime
FROM python:3.10-slim-bullseye

RUN apt-get update \
    && apt-get install -y --no-install-recommends git openssh-client procps libpq5 sqlite3\
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /
COPY . .

CMD  ["/bin/sh", "/entrypoint.sh"]
