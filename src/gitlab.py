from config import Config, GitProvider
import requests
from filehandler import mkdir
from gitlib import check_name, mirror
from pathlib import Path
import json

DEFAULT_HOST = "https://gitlab.com/api/v4/"


def backup(config: Config) -> bool:

    if config.host is None or not config.host:
        config.host = DEFAULT_HOST

    user = next(get_json(config.host + "user/", config.token))
    username = user['username']

    for page in get_json(config.host + "projects?membership=true", config.token):
        for project in page:
            name = check_name(project["path"])
            owner = check_name(project["namespace"]["path"])
            clone_url = project["http_url_to_repo"]

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
            url, headers={"PRIVATE-TOKEN": str(token)}
        )
        response.raise_for_status()
        yield json.loads(response.text)

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]
