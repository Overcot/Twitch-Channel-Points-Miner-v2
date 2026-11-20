# ---- build stage: compilers live only here ----
FROM python:3.15-slim-trixie AS builder

ARG BUILDX_QEMU_ENV
# Set to true to bundle flask+pandas for the analytics dashboard (heavy).
ARG WITH_ANALYTICS=false

WORKDIR /build
COPY ./requirements.txt ./requirements-analytics.txt ./

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Toolchain is needed only on platforms without prebuilt wheels (e.g. linux/arm/v7).
RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -qq -y --no-install-recommends \
    gcc g++ make cmake ninja-build libffi-dev libssl-dev zlib1g-dev python3-dev \
  && if [ "${BUILDX_QEMU_ENV}" = "true" ] && [ "$(getconf LONG_BIT)" = "32" ]; then \
        pip install --prefix=/install cryptography==3.3.2; \
     fi \
  && pip install --prefix=/install -r requirements.txt \
  && if [ "${WITH_ANALYTICS}" = "true" ]; then \
        pip install --prefix=/install -r requirements-analytics.txt; \
     fi \
  && rm -rf /var/lib/apt/lists/*

# ---- runtime stage: no compilers, no apt cache ----
FROM python:3.15-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MALLOC_ARENA_MAX=2

WORKDIR /usr/src/app

COPY --from=builder /install /usr/local
COPY ./TwitchChannelPointsMiner ./TwitchChannelPointsMiner

ENTRYPOINT [ "python", "run.py" ]
