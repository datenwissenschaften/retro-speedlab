FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704 AS requirements
COPY core/pyproject.toml /
RUN python -c "import tomllib; dependencies = tomllib.load(open('/pyproject.toml', 'rb'))['project']['dependencies']; \
open('/requirements.txt', 'w').write('\n'.join(dependencies))"

FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg libgl1 libglib2.0-0 git openssh-client curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://claude.ai/install.sh | bash && pip install pytest ruff yt-dlp
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /opt/retro-speedlab-core
COPY --from=requirements /requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip env -u PIP_NO_CACHE_DIR pip install --timeout 120 --retries 10 \
        --requirement requirements.txt
COPY core/ ./
RUN pip install --no-deps .
WORKDIR /app
COPY app/ ./
CMD ["python", "app.py"]
