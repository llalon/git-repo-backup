from config import Config, GitProvider
import requests
from filehandler import mkdir
from gitlib import check_name, mirror
from pathlib import Path

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

            # Check if this one is in the whitelist, or if whitelist is empty allow
            if not (not config.owners or config.owners is None):
                if owner not in config.owners:
                    continue

            if not (not config.repos or config.repos is None):
                if name not in config.repos:
                    continue

            owner_path = Path(config.directory, Path(owner))
            mkdir(owner_path)

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
