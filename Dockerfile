# ---- build stage: compilers live only here ----
FROM python:3.15-slim-trixie AS builder

# Set to true to bundle flask+pandas for the analytics dashboard (heavy).
ARG WITH_ANALYTICS=false

WORKDIR /build
COPY ./requirements.txt ./requirements-analytics.txt ./

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# The default dependencies are pure Python, so no compiler is needed.
# Analytics (pandas/numpy) may have to be built from source on platforms without wheels (e.g. linux/arm/v7).
RUN pip install --prefix=/install -r requirements.txt \
  && if [ "${WITH_ANALYTICS}" = "true" ]; then \
        apt-get update \
        && DEBIAN_FRONTEND=noninteractive apt-get install -qq -y --no-install-recommends \
            gcc g++ make cmake ninja-build libffi-dev libssl-dev zlib1g-dev python3-dev \
        && pip install --prefix=/install -r requirements-analytics.txt \
        && rm -rf /var/lib/apt/lists/*; \
     fi

# ---- runtime stage: no compilers, no apt cache ----
FROM python:3.15-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MALLOC_ARENA_MAX=2

WORKDIR /usr/src/app

COPY --from=builder /install /usr/local
COPY ./TwitchChannelPointsMiner ./TwitchChannelPointsMiner

ENTRYPOINT [ "python", "run.py" ]
