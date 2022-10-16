import requests
from pathlib import Path

from git_repo_backup.config import Config
from git_repo_backup.logger import log_message, log_error
from git_repo_backup.filehandler import mkdir
from git_repo_backup.gitlib import check_name, mirror

DEFAULT_HOST = "https://api.github.com/"


def backup(config: Config) -> bool:

    if config.host is None or not config.host:
        config.host = DEFAULT_HOST

    user = next(get_json(config.host + "user", config.token))
    username = user["login"]

    for page in get_json(config.host + "user/repos", config.token):
        for repo in page:
            name = check_name(repo["name"])
            owner = check_name(repo["owner"]["login"])
            clone_url = repo["clone_url"]

            if name is None:
                log_error("Skipping... Invalid name: '{0}'".format(repo["name"]))
                continue

            # Check if this one is in the whitelist, or if whitelist is empty allow
            if not (not config.owners or config.owners is None):
                if owner not in config.owners:
                    continue

            if not (not config.repos or config.repos is None):
                if name not in config.repos:
                    continue

            owner_path = Path(config.directory, Path(owner))
            mkdir(owner_path)

            log_message("Backing up repo: '{0}'".format(clone_url))

            mirror(name, clone_url, owner_path, username, config.token)

    return True


def get_json(url: str, token: str) -> dict:
    while True:
        response = requests.get(
            url, headers={"Authorization": "token {0}".format(token)}
        )
        response.raise_for_status()
        yield response.json()

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]
