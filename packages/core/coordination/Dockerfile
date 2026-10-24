FROM python:3.12.15-bookworm@sha256:dc0705844ae55b4c07e4c06de75c4e706ca7debfbb9ce017bdceeb3922ea5c29 AS sqlite-builder
RUN install -d -m 0700 -o 10002 -g 10002 /build
COPY --chmod=0444 packages/core/coordination/build_sqlite.py /build/build_sqlite.py
COPY --chmod=0444 packages/core/coordination/build-inputs/sqlite-amalgamation-3510300.zip /build/sqlite-amalgamation-3510300.zip
USER 10002:10002
RUN python3 /build/build_sqlite.py --build --archive /build/sqlite-amalgamation-3510300.zip --output /build/sqlite

FROM python:3.12.15-slim-bookworm@sha256:57d96f71de145a98e7ceca18ee4ade77bba4103a33a72dfaea026b23625c6bf0
ARG SOURCE_REV
LABEL org.opencontainers.image.title="Palarran Coordination API" org.opencontainers.image.revision=$SOURCE_REV
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 LD_LIBRARY_PATH=/opt/palarran-sqlite
WORKDIR /app
RUN install -d -m 0755 /opt/palarran-sqlite
COPY --from=sqlite-builder --chmod=0444 /build/sqlite/libsqlite3.so.0 /opt/palarran-sqlite/libsqlite3.so.0
COPY --from=sqlite-builder --chmod=0444 /build/sqlite/receipt.json /opt/palarran-sqlite/receipt.json
COPY --chmod=0444 packages/core/coordination/service.py /app/service.py
COPY --chmod=0444 packages/core/coordination/share.py packages/core/coordination/share_store.py /app/
COPY --chmod=0444 packages/infrastructure/hosting/runtime.py /app/container.py
USER 10002:10002
ENTRYPOINT ["python3", "-B", "/app/container.py", "coordination"]
CMD ["serve"]
