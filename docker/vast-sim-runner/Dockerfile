# Minimal Vast runner image — Newton JSON entrypoint.
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN pip install --no-cache-dir newton rebound numpy
COPY newton_runner.py /app/newton_runner.py
COPY vast_remote_runner_standalone.py /app/vast_remote_runner.py
ENV WARP_CACHE_DIR=/tmp/warp-cache
ENTRYPOINT ["python", "/app/vast_remote_runner.py"]
CMD ["--config", "/tmp/c4_sim_config.json"]
