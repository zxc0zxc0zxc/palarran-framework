FROM python:3.12.15-slim-bookworm@sha256:57d96f71de145a98e7ceca18ee4ade77bba4103a33a72dfaea026b23625c6bf0
ARG SOURCE_REV
LABEL org.opencontainers.image.title="Palarran Memory API" org.opencontainers.image.revision=$SOURCE_REV
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --chmod=0444 packages/memory/knowledge/runtime/service.py /app/service.py
COPY --chmod=0444 packages/infrastructure/hosting/runtime.py /app/container.py
USER 10001:10001
ENTRYPOINT ["python3", "-B", "/app/container.py", "memory"]
CMD ["serve"]
