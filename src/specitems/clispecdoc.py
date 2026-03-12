# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to generate a specification type
documentation.
"""

# Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG
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
import sys

from .contentmarkdown import MarkdownContent, MarkdownMapper
from .contentsphinx import SphinxContent, SphinxMapper
from .items import (ItemCache, ItemCacheConfig, ItemTypeProvider,
                    SpecTypeProvider)
from .specdoc import SpecDocumentConfig, generate_specification_documentation

_DOC_FORMAT = {
    "markdown": (MarkdownContent, MarkdownMapper),
    "rest": (SphinxContent, SphinxMapper)
}


def clispecdoc(argv: list[str], type_provider: ItemTypeProvider) -> None:
    """ Document the specification item format using the type provider. """
    parser = argparse.ArgumentParser(description=clispecdocitems.__doc__)
    parser.add_argument('--format',
                        choices=["markdown", "rest"],
                        type=str.lower,
                        default="markdown",
                        help="the output format")
    parser.add_argument("--root-type-uid",
                        default="/spec/root",
                        help="the UID of the specification format root type")
    parser.add_argument(
        "--ignore",
        default="^$",
        help="the regular expression used to ignore types by name")
    parser.add_argument("--label-prefix",
                        default="SpecType",
                        help="the label prefix")
    parser.add_argument("--section-label-prefix",
                        default="",
                        help="the section label prefix")
    parser.add_argument(
        "--hierarchy-text",
        default="The specification item types have the following hierarchy:",
        help="the specification type hierarchy prologue text")
    parser.add_argument("--section-name",
                        default="Specification items",
                        help="the section name")
    parser.add_argument(
        "--hierarchy-subsection-name",
        default="Specification item hierarchy",
        help="the specification type hierarchy subsection name")
    parser.add_argument("--item-types-subsection-name",
                        default="Specification item types",
                        help="the item types subsection name")
    parser.add_argument("--value-types-subsection-name",
                        default="Specification attribute sets and value types",
                        help="the value and types subsection name")
    parser.add_argument("target",
                        metavar="TARGET",
                        nargs=1,
                        default=["docs/source/items.rst"],
                        help="the documentation target file")
    args = parser.parse_args(argv[1:])
    item_cache_config = ItemCacheConfig(spec_type_root_uid="/spec/root")
    item_cache = ItemCache(item_cache_config, type_provider=type_provider)
    spec_doc_config = SpecDocumentConfig(
        target=args.target[0],
        root_type_uid=args.root_type_uid,
        ignore=args.ignore,
        label_prefix=args.label_prefix,
        section_label_prefix=args.section_label_prefix,
        hierarchy_text=args.hierarchy_text,
        section_name=args.section_name,
        hierarchy_subsection_name=args.hierarchy_subsection_name,
        item_types_subsection_name=args.item_types_subsection_name,
        value_types_subsection_name=args.value_types_subsection_name)
    create_content, create_mapper = _DOC_FORMAT[args.format]
    generate_specification_documentation(
        spec_doc_config, item_cache,
        create_mapper(next(iter(item_cache.values()))), create_content)


def clispecdocitems(argv: list[str] = sys.argv) -> None:
    """ Document the specification item format. """
    clispecdoc(argv, SpecTypeProvider({}))
