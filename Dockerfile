# Same image runs locally and in CI so the gate is reproducible.
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY prompts ./prompts
COPY data ./data
COPY pyproject.toml .

# Run the gate; non-zero exit blocks a release.
ENTRYPOINT ["python", "-m", "app.cli"]
CMD ["--baseline", "v1_production", "--candidate", "v2_candidate"]
