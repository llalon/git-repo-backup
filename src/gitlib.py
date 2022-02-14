import re
import subprocess
from pathlib import Path
import urllib.parse
from filehandler import mkdir


def check_name(name: str):
    if not re.match(r"^\w[-\.\w]*$", name):
        raise RuntimeError("invalid name '{0}'".format(name))
    return name


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


