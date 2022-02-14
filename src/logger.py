import sys


def log_message(message: str):
    log("INFO: " + str(message) + "\n")


def log_error(message: str):
    log("ERROR: " + str(message) + "\n")


def log(message: str):
    print(str(message), file=sys.stderr)
