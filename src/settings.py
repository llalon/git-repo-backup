import os

ENV_VAR = "BACKUP_DIR"
DEFAULT_SAVE_DIR = "./"


def get_save_dir_from_env() -> str:
    d = os.environ[ENV_VAR]

    if d is None:
        return DEFAULT_SAVE_DIR
    else:
        return str(d)
