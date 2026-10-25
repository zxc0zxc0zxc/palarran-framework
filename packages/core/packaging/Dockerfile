FROM python:3.12.15-slim-bookworm@sha256:57d96f71de145a98e7ceca18ee4ade77bba4103a33a72dfaea026b23625c6bf0
ARG SOURCE_REV
LABEL org.opencontainers.image.title="Palarran Packaging Registry" org.opencontainers.image.revision=$SOURCE_REV
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --chmod=0444 packages/core/packaging/__init__.py /app/packages/core/packaging/__init__.py
COPY --chmod=0444 packages/core/packaging/contract.py /app/packages/core/packaging/contract.py
COPY --chmod=0444 packages/core/packaging/storage.py /app/packages/core/packaging/storage.py
COPY --chmod=0444 packages/core/packaging/store.py /app/packages/core/packaging/store.py
COPY --chmod=0444 packages/core/packaging/service.py /app/packages/core/packaging/service.py
USER 10001:10001
ENTRYPOINT ["python3", "-B", "-m", "packages.core.packaging.service"]
CMD ["--db", "/state/registry.sqlite3", "--blobs", "/state/blobs", "--credentials", "/run/secrets/registry.json", "--port", "18793", "--container-network"]
