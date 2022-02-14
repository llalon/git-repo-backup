#!/usr/bin/env python3

import json
import argparse
from config import Config, GitProvider, validate_config, parse_config
import sys
from gitlab import backup as gitlab
from github import backup as github
from filehandler import mkdir
from logger import log_error, log_message


def backup(config: Config) -> bool:
    if not validate_config(config):
        log_error("Config invalid: {0}".format(str(config)))
        return False

    if mkdir(config.directory):
        log_message("Created directory: {0}".format(config.directory))

    if config.method == GitProvider.github:
        return github(config)
    elif config.method == GitProvider.gitlab:
        return gitlab(config)
    else:
        return False


def main():
    parser = argparse.ArgumentParser(description="Backup Git repositories")
    parser.add_argument("config", metavar="CONFIG", help="The configuration file", default=None, nargs='?')
    args = parser.parse_args()

    if args.config is None:
        configs = json.load(sys.stdin)
    else:
        with open(args.config, "r") as f:
            configs = json.loads(f.read())

    if len(configs) == 0 or configs is None:
        log_error("In-valid config")
        sys.exit(0)

    for config in configs:
        backup(parse_config(config))

    sys.exit(1)


if __name__ == '__main__':
    main()
