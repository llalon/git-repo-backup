#!/usr/bin/env python3

import os
import re
import sys
import json
import errno
import argparse
import subprocess
import urllib.parse
import requests
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

ERROR_INVALID_NAME = 123
DEFAULT_HOST_GITHUB = "https://api.github.com/"
DEFAULT_HOST_GITLAB = "https://gitlab.com/api/v4/"

# Directory hard coded to /data/ as this is made to be run in docker... Use outside should change accordingly.
SAVE_BASE_DIR = Path("./backup")


class GitProvider(Enum):
    gitlab = auto()
    github = auto()


@dataclass
class Config:
    token: str
    owners: list[str]
    directory: Path
    method: GitProvider
    repos: list[str]
    host: str


def check_name(name: str):
    if not re.match(r"^\w[-\.\w]*$", name):
        raise RuntimeError("invalid name '{0}'".format(name))
    return name


def mkdir(path: Path) -> bool:
    try:
        os.makedirs(str(path.absolute()), 0o770)
    except OSError as ose:
        if ose.errno != errno.EEXIST:
            raise
        return False
    return True


def is_pathname_valid(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    """

    try:
        if not isinstance(pathname, str) or not pathname:
            return False
        _, pathname = os.path.splitdrive(pathname)

        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)

        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError as exc:
        return False
    else:
        return True


def is_path_creatable(pathname: str) -> bool:
    """
    `True` if the current user has sufficient permissions to create the passed
    pathname; `False` otherwise.
    """

    dirname = os.path.dirname(pathname) or os.getcwd()
    return os.access(dirname, os.W_OK)


def is_path_exists_or_creatable(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS _and_
    either currently exists or is hypothetically creatable; `False` otherwise.

    This function is guaranteed to _never_ raise exceptions.
    """

    try:
        return is_pathname_valid(pathname) and (
                os.path.exists(pathname) or is_path_creatable(pathname))
    except OSError:
        return False


def mirror(repo_name: str, repo_url: str, to_path: Path, username: str, token: str):
    parsed = urllib.parse.urlparse(repo_url)
    modified = list(parsed)
    modified[1] = "{username}:{token}@{netloc}".format(
        username=username, token=token, netloc=parsed.netloc
    )
    repo_url = urllib.parse.urlunparse(modified)

    repo_path = Path(to_path, Path(repo_name))
    mkdir(repo_path)

    # git-init manual:
    # "Running git init in an existing repository is safe."
    subprocess.call(["git", "init", "--bare", "--quiet"], cwd=repo_path.absolute())

    # https://github.com/blog/1270-easier-builds-and-deployments-using-git-over-https-and-oauth:
    # "To avoid writing tokens to disk, don't clone."
    subprocess.call(
        [
            "git",
            "fetch",
            "--force",
            "--prune",
            "--tags",
            repo_url,
            "refs/heads/*:refs/heads/*",
        ],
        cwd=repo_path.absolute(),
    )


def get_json_github(url: str, token: str) -> dict:
    while True:
        response = requests.get(
            url, headers={"Authorization": "token {0}".format(token)}
        )
        response.raise_for_status()
        yield response.json()

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]


def backup(config: Config) -> bool:
    if not validate_config(config):
        print("Config invalid: {0}".format(str(config)), file=sys.stderr)
        return False

    if mkdir(config.directory):
        print("Created directory: {0}".format(config.directory), file=sys.stderr)

    if config.method == GitProvider.github:
        return backup_github(config)
    elif config.method == GitProvider.gitlab:
        return backup_gitlab(config)
    else:
        return False


def backup_github(config: Config) -> bool:
    user = next(get_json_github(config.host + "user", config.token))
    username = user["login"]

    for page in get_json_github(config.host + "user/repos", config.token):
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


def get_json_gitlab(url: str, token: str) -> dict:
    while True:
        response = requests.get(
            url, headers={"PRIVATE-TOKEN": str(token)}
        )
        response.raise_for_status()
        yield json.loads(response.text)

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]


def backup_gitlab(config: Config) -> bool:

    user = next(get_json_gitlab(config.host + "user/", config.token))
    username = user['username']

    for page in get_json_gitlab(config.host + "projects?membership=true", config.token):
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


def parse_config(config: dict) -> Config:

    token = config['token']
    directory = Path(config['directory']) if config.get('directory', None) is not None else Path("./")
    host = config['host'] if config.get('host', None) is not None else None
    owners = config['owners'] if config.get('owners', None) is not None else []
    repos = config['repos'] if config.get('repos', None) is not None else []

    try:
        method = GitProvider[config['method']]
    except():
        method = None

    # Provide default hosts if non were provided
    if host is None:
        if method is GitProvider.github:
            host = DEFAULT_HOST_GITHUB
        elif method is GitProvider.gitlab:
            host = DEFAULT_HOST_GITLAB
        else:
            host = None

    # Append base path
    directory_full = Path(SAVE_BASE_DIR, directory)

    return Config(token, owners, directory_full, method, repos, host)


def validate_config(config: Config) -> bool:
    if not config.token:
        return False

    if not is_path_exists_or_creatable(str(config.directory.absolute().parent)):
        return False

    if not config.host:
        return False

    if config.host is None:
        return False

    if config.method is None:
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Backup Git repositories")
    parser.add_argument("config", metavar="CONFIG", help="The configuration file")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        configs = json.loads(f.read())

    for config in configs:
        backup(parse_config(config))


if __name__ == '__main__':
    main()
