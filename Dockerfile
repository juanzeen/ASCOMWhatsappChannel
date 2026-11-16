FROM ghcr.io/astral-sh/uv:latest AS uv

FROM devlikeapro/waha:gows

COPY --from=uv /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --frozen --no-dev

COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000 3000

CMD ["./entrypoint.sh"]
