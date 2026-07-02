# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to verify the specification item format.
"""

# Copyright (C) 2026 embedded brains GmbH & Co. KG
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

import importlib.metadata
import logging
from pathlib import Path
import sys

from .cliutil import get_arguments
from .items import (ItemCache, ItemCacheConfig, ItemDataByUID,
                    ItemTypeProvider, SpecTypeProvider)
from .specformatter import SpecYAMLFormatter
from .specverify import verify_specification_format


# Packages using specitems can register their types through the following
# plugin mechanism.  They have to add something like this to their
# `pyproject.toml` file:
#
# [project.entry-points."specitems_type_provider.plugins"]
# mypackage = "mypackage.mymodule:load_mypackage_types"
def _create_type_provider() -> ItemTypeProvider:
    data_by_uid: ItemDataByUID = {}
    for ep in importlib.metadata.entry_points(
            group="specitems_type_provider.plugins"):
        load_types = ep.load()
        data_by_uid.update(load_types())
    return SpecTypeProvider(data_by_uid)


def cliverify(argv: list[str] = sys.argv) -> int:
    """
    Verify the specification item format and optionally format the items.
    """

    def _add_arguments(parser):
        parser.add_argument("--format-items",
                            action="store_true",
                            help="format the items")
        parser.add_argument("--clang-format-path",
                            default="clang-format",
                            help="the path to the clang-format executable")
        parser.add_argument(
            "--clang-format-style",
            action="append",
            default=[],
            metavar="CLANG_FORMAT_STYLE",
            help="a clang-format style name used by the "
            "specification types and, separated by a colon, "
            "the associated clang-format style "
            "file (example: file-scope:.clang-format); "
            "the style name is not related to the built-in styles "
            "of clang-format; this option can be given multiple times")
        parser.add_argument("--do-not-indent-lists",
                            action="store_true",
                            help="do not indent lists in the YAML output")
        parser.add_argument("spec_items_or_directories",
                            nargs="+",
                            metavar="SPEC_ITEM_OR_DIRECTORY",
                            help="specification item file or directory")

    args = get_arguments(argv[1:],
                         default_log_level="WARNING",
                         description=cliverify.__doc__,
                         add_arguments=(_add_arguments, ))
    uid_log_level = logging.ERROR
    item_files: list[str] = []
    spec_dirs: list[str] = []
    for path in args.spec_items_or_directories:
        if Path(path).is_file():
            uid_log_level = logging.INFO
            item_files.append(path)
        else:
            spec_dirs.append(path)
    config = ItemCacheConfig(paths=spec_dirs)
    item_cache = ItemCache(config, type_provider=_create_type_provider())
    for path in item_files:
        item_cache.add_item_from_file(path, path, initialize_links=False)
    clang_format_style: dict[str, str] = {}
    for style_file in args.clang_format_style:
        style, sep, file = style_file.partition(":")
        if not sep or not style or not file:
            logging.error(
                "the --clang-format-style option value '%s' "
                "is not in <name>:<path> format", style_file)
            return 1
        clang_format_style[style] = file
    if args.format_items:
        formatter = SpecYAMLFormatter(
            clang_format_path=args.clang_format_path,
            clang_format_style=clang_format_style,
            indent_lists=not args.do_not_indent_lists)
    else:
        formatter = None
    return verify_specification_format(item_cache,
                                       uid_log_level=uid_log_level,
                                       formatter=formatter).exit_code()
