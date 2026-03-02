# SPDX-License-Identifier: BSD-2-Clause
""" The specitems package. """

# Copyright (C) 2019, 2026 embedded brains GmbH & Co. KG
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

from .cite import BibTeXCitationProvider
from .cliutil import (
    create_argument_parser,
    create_config,
    init_logging,
    load_config,
)
from .content import (
    Content,
    ContentAddContext,
    Copyright,
    Copyrights,
    GenericContent,
    GenericContentIterable,
    MARKDOWN_ROLES,
    get_value_plural,
    list_terms,
    make_copyright_statement,
    split_copyright_statement,
    to_camel_case,
)
from .contenttext import (
    TextContent,
    TextMapper,
    latex_escape,
    make_label,
)
from .contentmarkdown import (
    MarkdownContent,
    MarkdownMapper,
)
from .contentsphinx import (
    SphinxContent,
    SphinxMapper,
    escape_code_line,
    get_reference,
)
from .getvaluesubprocess import get_value_subprocess
from .glossary import (
    DocumentGlossaryConfig,
    GlossaryConfig,
    augment_glossary_terms,
    generate_glossary,
)
from .hashutil import (
    base64_to_hex,
    base64_to_hex_text,
    hash_file,
    hash_file_lines,
    hash_file_lines_md5,
    hash_file_lines_sha256,
    hash_file_md5,
    hash_file_sha256,
)
from .items import (
    EmptyItem,
    EmptyItemCache,
    EnabledSet,
    IS_ENABLED_OPS,
    IsEnabled,
    IsLinkEnabled,
    Item,
    ItemCache,
    ItemCacheConfig,
    ItemDataByUID,
    ItemSelection,
    ItemType,
    ItemTypeProvider,
    ItemView,
    ItemViewGetMissing,
    JSONItemCache,
    Link,
    SpecTypeProvider,
    create_unique_link,
    data_digest,
    is_enabled,
    is_enabled_with_ops,
    item_is_enabled,
    link_is_enabled,
    load_data,
    load_data_by_uid,
    pickle_load_data_by_uid,
    save_data,
    to_collection,
    to_iterable,
)
from .itemmapper import (
    ItemGetValue,
    ItemGetValueContext,
    ItemGetValueMap,
    ItemMapper,
    ItemValueProvider,
    get_value_default,
    unpack_arg,
)
from .specdoc import SpecDocumentConfig, generate_specification_documentation
from .specverify import (
    SpecVerifier,
    VerifyStatus,
    verify_specification_format,
)
from .subprocessaction import (
    make_subprocess_environment,
    run_subprocess_action,
)

__all__ = [
    "BibTeXCitationProvider",
    "Content",
    "ContentAddContext",
    "Copyright",
    "Copyrights",
    "DocumentGlossaryConfig",
    "EmptyItem",
    "EmptyItemCache",
    "EnabledSet",
    "GenericContent",
    "GenericContentIterable",
    "GlossaryConfig",
    "IS_ENABLED_OPS",
    "IsEnabled",
    "IsLinkEnabled",
    "Item",
    "ItemCache",
    "ItemCacheConfig",
    "ItemDataByUID",
    "ItemGetValue",
    "ItemGetValueContext",
    "ItemGetValueMap",
    "ItemMapper",
    "ItemSelection",
    "ItemType",
    "ItemTypeProvider",
    "ItemValueProvider",
    "ItemView",
    "ItemViewGetMissing",
    "JSONItemCache",
    "Link",
    "MARKDOWN_ROLES",
    "MarkdownContent",
    "MarkdownMapper",
    "SpecDocumentConfig",
    "SpecTypeProvider",
    "SpecVerifier",
    "SphinxContent",
    "SphinxMapper",
    "TextContent",
    "TextMapper",
    "VerifyStatus",
    "augment_glossary_terms",
    "base64_to_hex",
    "base64_to_hex_text",
    "create_argument_parser",
    "create_config",
    "create_unique_link",
    "data_digest",
    "escape_code_line",
    "generate_glossary",
    "generate_specification_documentation",
    "get_reference",
    "get_value_default",
    "get_value_plural",
    "get_value_subprocess",
    "hash_file",
    "hash_file_lines",
    "hash_file_lines_md5",
    "hash_file_lines_sha256",
    "hash_file_md5",
    "hash_file_sha256",
    "init_logging",
    "is_enabled",
    "is_enabled_with_ops",
    "item_is_enabled",
    "latex_escape",
    "link_is_enabled",
    "list_terms",
    "load_config",
    "load_data",
    "load_data_by_uid",
    "make_copyright_statement",
    "make_label",
    "make_subprocess_environment",
    "pickle_load_data_by_uid",
    "run_subprocess_action",
    "save_data",
    "split_copyright_statement",
    "to_camel_case",
    "to_collection",
    "to_iterable",
    "unpack_arg",
    "verify_specification_format",
]
