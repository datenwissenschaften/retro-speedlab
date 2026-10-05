FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install --yes --no-install-recommends ffmpeg libgl1 libglib2.0-0 git openssh-client curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://claude.ai/install.sh | bash && pip install pytest ruff yt-dlp
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app
COPY pyproject.toml ./
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" \
        > requirements.txt \
    && pip install --requirement requirements.txt
COPY . ./
RUN python -m stable_retro.import roms
RUN sed -i 's/^  host: 127.0.0.1$/  host: 0.0.0.0/' config.yaml && grep -q '^  host: 0.0.0.0$' config.yaml
EXPOSE 18080
CMD ["python", "app.py"]
