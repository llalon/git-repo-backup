import sys


def log_message(message: str):
    log("INFO: " + str(message))


def log_error(message: str):
    log("ERROR: " + str(message))


def log(message: str):
    print(str(message), file=sys.stderr)
