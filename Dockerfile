#TAG docker.io/llalon/git-repo-backup
FROM debian:bullseye-slim AS base

WORKDIR /tmp
COPY requirements.txt ./
RUN apt-get update && \
    apt-get install -y python3-pip python3 python-is-python3 git
RUN pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

FROM base AS build
WORKDIR /app
COPY src/ ./
RUN stickytape main.py --add-python-path . --output-file /app/git-repo-backup.py

FROM base AS final
ENV BACKUP_DIR="/backup"
COPY --from=build /app/git-repo-backup.py /bin/git-repo-backup.py
RUN chmod +x /bin/git-repo-backup.py

ENTRYPOINT ["python3", "/bin/git-repo-backup.py"]
