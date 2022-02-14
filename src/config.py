from dataclasses import dataclass
from pathlib import Path
from enum import Enum, auto
from filehandler import is_path_exists_or_creatable
import settings


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


def validate_config(config: Config) -> bool:
    if not config.token:
        return False

    if not is_path_exists_or_creatable(str(config.directory.absolute().parent)):
        return False

    if config.method is None:
        return False

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

    # Append base path
    directory_full = Path(settings.get_save_dir_from_env(), directory)

    return Config(token, owners, directory_full, method, repos, host)
