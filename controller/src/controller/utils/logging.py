# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
import sys
import time
from typing import Any


def configure_logging(
    path_to_log_folder: str | None = None,
    log_file_prefix: str | None = None,
    log_level: int = logging.INFO,
    logging_formatter: logging.Formatter | None = None,
) -> None:
    """Apply standard configuration to logging.

    Args:
        path_to_log_folder: optional path to an existing folder in which a log file will be created and used instead of stdout. log_file_prefix must also be specified if this argument is not None.
        log_file_prefix: if path_to_log_folder is specified, will write logs to file in the given log folder using this as the prefix of the filename.
        log_level: set the desired logging threshold level
        logging_format: the desired format of logging output. 'standard' should be used in all cases except for when used in a notebook.
        logging_formatter: optional custom formatter to set on each logging handler. Useful as a catch-all in situations where information must be redacted from log files.
    """
    logging.Formatter.converter = time.gmtime  # ensure all logging timestamps are UTC

    handlers: list[Any] = list()
    if path_to_log_folder is not None:
        if not os.path.isdir(path_to_log_folder):
            raise ValueError(f"Log folder does not exist: {path_to_log_folder}")
        file_handler = logging.FileHandler(
            os.path.join(
                path_to_log_folder,
                f'{log_file_prefix}__{datetime.datetime.utcnow().strftime("%Y_%m_%d_%H%M%S")}_controller.txt',
            )
        )
        handlers.append(file_handler)
    else:
        handlers.append(logging.StreamHandler(sys.stdout))

    config_format = "[%(asctime)s UTC] %(name)s-{%(filename)s:%(lineno)d} %(levelname)s - %(message)s"

    if logging_formatter is not None:
        for handler in handlers:
            handler.setFormatter(logging_formatter)

    logging.basicConfig(level=log_level, format=config_format, handlers=handlers)


def redact_sensitive_info_from_path(file_path: str | None) -> str | None:
    """Scrubs username from file path to protect sensitive info."""
    # TODO is None really ever passed into this function?
    if file_path is None:
        return None
    split_path = re.split(r"(Users\\)(.*)(\\AppData)", file_path)
    if len(split_path) != 5:
        return get_redacted_string(4)
    scrubbed_path = split_path[0] + split_path[1]
    scrubbed_path += get_redacted_string(len(split_path[2]))
    scrubbed_path += split_path[3] + split_path[4]
    return scrubbed_path


def get_redacted_string(length: int) -> str:
    return "*" * length
