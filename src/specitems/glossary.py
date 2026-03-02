# SPDX-License-Identifier: BSD-2-Clause
""" Provides functions for glossary of terms generation. """

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

import dataclasses
import glob
import re
from typing import Any, Callable, NamedTuple, Optional, Pattern

from .contenttext import TextContent
from .items import Item, ItemCache
from .itemmapper import ItemGetValueContext, ItemMapper

_ItemMap = dict[str, Item]


@dataclasses.dataclass
class DocumentGlossaryConfig:
    """ Represents a document-specific glossary configuration. """
    target: str = "glossary.md"
    header: str = "Glossary"
    md_source_paths: list[str] = dataclasses.field(default_factory=list)
    rest_source_paths: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class GlossaryConfig:
    """ Represents a glossary configuration. """
    project_target: str | None = None
    project_header: str = "Glossary"
    project_groups: list[str] = dataclasses.field(default_factory=list)
    documents: list[DocumentGlossaryConfig] = dataclasses.field(
        default_factory=list)


class _Glossary(NamedTuple):
    """ A glossary of terms. """
    uid_to_item: _ItemMap
    term_to_item: _ItemMap


def augment_glossary_terms(item: Item, path: list[str]) -> None:
    """
    Augment the glossary term items of the cache with a glossary path prefix.
    """
    for child in item.children("requirement-refinement"):
        augment_glossary_terms(child, path + [child["name"]])
    for child in item.children("glossary-member"):
        term = " - ".join(path + [child["term"]])
        child.view["term"] = term


def _gather_glossary_terms(item: Item, glossary: _Glossary) -> None:
    for child in item.children("requirement-refinement"):
        _gather_glossary_terms(child, glossary)
    for child in item.children("glossary-member"):
        glossary.uid_to_item[child.uid] = child
        term = child.view["term"]
        assert term not in glossary.term_to_item
        glossary.term_to_item[term] = child


def _generate_glossary_content(
        terms: _ItemMap, header: str, target: str, mapper: ItemMapper,
        create_content: Callable[[], TextContent]) -> None:
    content = create_content()
    with content.section(header):
        with content.directive("glossary"):
            for item in sorted(terms.values(),
                               key=lambda x: x.view["term"].lower()):
                content.register_license_and_copyrights_of_item(item)
                text = mapper.substitute(item["text"], item)
                content.add_glossary_term(item.view["term"], text)
    content.add_licence_and_copyrights()
    content.write(target, beautify=True)


_MD_TERM = re.compile(r"{term}`([^`]+)`")
_REST_TERM = re.compile(r":term:`([^`]+)`")
_TERM_2 = re.compile(r"^[^<]+<([^>]+)>")
_SPACE = re.compile(r"\s+")


def _find_glossary_terms(path: str, document_terms: _ItemMap,
                         glossary: _Glossary, file_extension: str,
                         term_pattern: Pattern) -> None:
    for src in glob.glob(path + f"/**/*{file_extension}", recursive=True):
        if src.endswith(f"glossary{file_extension}"):
            continue
        with open(src, "r", encoding="utf-8") as out:
            for term in term_pattern.findall(out.read()):
                match = _TERM_2.search(term)
                if match:
                    term = match.group(1)
                term = _SPACE.sub(" ", term)
                item = glossary.term_to_item[term]
                document_terms[item.uid] = item


class _GlossaryMapper(ItemMapper):

    def __init__(self, item: Item, document_terms: _ItemMap):
        super().__init__(item)
        self._document_terms = document_terms
        self.add_get_value("glossary/term:/term", self._add_to_terms)
        self.add_get_value("glossary/term:/plural", self._add_to_terms)

    def map(self,
            identifier: str,
            item: Optional[Item] = None,
            prefix: str = "") -> tuple[Item, str, Any]:
        try:
            return super().map(identifier, item, prefix)
        except ValueError:
            return self.item, "", ""

    def _add_to_terms(self, ctx: ItemGetValueContext) -> str:
        if ctx.item.uid not in self._document_terms:
            self._document_terms[ctx.item.uid] = ctx.item
            _GlossaryMapper(ctx.item,
                            self._document_terms).substitute(ctx.item["text"])
        # The value of this substitute is unused.
        return ""


def _resolve_glossary_terms(document_terms: _ItemMap) -> None:
    for term in list(document_terms.values()):
        _GlossaryMapper(term, document_terms).substitute(term["text"])


def _generate_project_glossary(
        glossary: _Glossary, header: str, target: Optional[str],
        mapper: ItemMapper, create_content: Callable[[], TextContent]) -> None:
    if target:
        _generate_glossary_content(glossary.uid_to_item, header, target,
                                   mapper, create_content)


def _generate_document_glossary(
        document_glossary: DocumentGlossaryConfig, glossary: _Glossary,
        mapper: ItemMapper, create_content: Callable[[], TextContent]) -> None:
    document_terms: _ItemMap = {}
    for path in document_glossary.md_source_paths:
        _find_glossary_terms(path, document_terms, glossary, ".md", _MD_TERM)
    for path in document_glossary.rest_source_paths:
        _find_glossary_terms(path, document_terms, glossary, ".rst",
                             _REST_TERM)
    _resolve_glossary_terms(document_terms)
    _generate_glossary_content(document_terms, document_glossary.header,
                               document_glossary.target, mapper,
                               create_content)


def generate_glossary(config: GlossaryConfig, item_cache: ItemCache,
                      mapper: ItemMapper,
                      create_content: Callable[[], TextContent]) -> None:
    """
    Generate glossaries of terms according to the configuration.

    Args:
        config: The glossary configuration.
        item_cache: The item cache containing the glossary groups and terms.
        mapper: The item mapper used for content substitutions.
        create_content: The content builder constructor.
    """
    project_glossary = _Glossary({}, {})
    for uid in config.project_groups:
        group = item_cache[uid]
        assert group.type == "glossary/group"
        _gather_glossary_terms(group, project_glossary)

    _generate_project_glossary(project_glossary, config.project_header,
                               config.project_target, mapper, create_content)

    for document_glossary in config.documents:
        _generate_document_glossary(document_glossary, project_glossary,
                                    mapper, create_content)
