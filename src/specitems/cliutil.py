# SPDX-License-Identifier: BSD-2-Clause
""" Provides utility functions for command line interfaces. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import argparse
import itertools
import logging
import os
from typing import Any, Callable, Iterable, Optional, Type, TypeVar

import yaml

_Config = TypeVar("_Config")


def create_config(config: dict, constructor: Type[_Config]) -> _Config:
    """ Create a configuration object from the configuration. """
    obj = constructor()
    for key, value in config.items():
        key = key.replace("-", "_")
        if not hasattr(obj, key):
            raise ValueError(f"{constructor} type has no attribute "
                             f"{key} present in configuration {config}")
        setattr(obj, key, value)
    return obj


def get_arguments(
    argv: list[str],
    default_log_level: str = "INFO",
    description: Optional[str] = None,
    add_arguments: Iterable[Callable[[argparse.ArgumentParser],
                                     None]] = tuple(),
    post_process_arguments: Iterable[Callable[[argparse.Namespace],
                                              None]] = tuple()
) -> argparse.Namespace:
    """
    Create an argument parser with default logging options, optionally add
    arguments to the parser, parse the argument vector, initialize logging,
    optionally post process the parsed arguments, and return the parsed
    arguments.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--log-level',
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        type=str.upper,
        default=default_log_level,
        help="log level")
    parser.add_argument('--log-file',
                        type=str,
                        default=None,
                        help="log to this file")
    parser.add_argument('--log-file-and-stderr',
                        action="store_true",
                        help="log to file and stderr")
    for add in add_arguments:
        add(parser)
    args = parser.parse_args(argv)
    init_logging(args)
    for post_process in post_process_arguments:
        post_process(args)
    return args


def _add_item_cache_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--spec-directories",
                        metavar="SPEC_DIRECTORY",
                        type=str,
                        action="extend",
                        default=None,
                        nargs="+",
                        help="a specification directory (default: spec)")
    parser.add_argument(
        "--cache-directory",
        help="the specification cache directory (default: spec-cache)",
        default="spec-cache")


def _post_process_item_cache_arguments(args: argparse.Namespace) -> None:
    if args.spec_directories is None:
        args.spec_directories = ["spec"]


def get_item_cache_arguments(
    argv: list[str],
    default_log_level: str = "INFO",
    description: Optional[str] = None,
    add_arguments: Iterable[Callable[[argparse.ArgumentParser],
                                     None]] = tuple(),
    post_process_arguments: Iterable[Callable[[argparse.Namespace],
                                              None]] = tuple()
) -> argparse.Namespace:
    """
    Create an argument parser with default logging and item cache options,
    optionally add arguments to the parser, parse the argument vector,
    initialize logging, optionally post process the parsed arguments, and
    return the parsed arguments.
    """
    return get_arguments(
        argv, default_log_level, description,
        itertools.chain((_add_item_cache_arguments, ), add_arguments),
        itertools.chain((_post_process_item_cache_arguments, ),
                        post_process_arguments))


def init_logging(args: argparse.Namespace) -> None:
    """ Initialize the logging module. """
    handlers: list = []
    if args.log_file is None:
        handlers.append(logging.StreamHandler())
    else:
        handlers.append(logging.FileHandler(args.log_file, mode="a"))
        if args.log_file_and_stderr:
            handlers.append(logging.StreamHandler())
    logging.basicConfig(level=args.log_level,
                        datefmt="%Y-%m-%dT%H:%M:%S",
                        force=True,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        handlers=handlers)


def load_config(config_filename: str) -> Any:
    """ Loads the configuration file with recursive includes. """

    class IncludeLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
        """ YAML loader customization to process custom include tags. """
        _filenames = [config_filename]

        def include(self, node):
            """ Processes the custom include tag. """
            container = IncludeLoader._filenames[0]
            dirname = os.path.dirname(container)
            filename = os.path.join(dirname, self.construct_scalar(node))
            IncludeLoader._filenames.insert(0, filename)
            with open(filename, "r", encoding="utf-8") as included_file:
                data = yaml.load(included_file, IncludeLoader)
            IncludeLoader._filenames.pop()
            return data

    IncludeLoader.add_constructor("!include", IncludeLoader.include)
    with open(config_filename, "r", encoding="utf-8") as config_file:
        return yaml.load(config_file.read(), Loader=IncludeLoader)
