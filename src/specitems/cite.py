# SPDX-License-Identifier: BSD-2-Clause
""" Provides an item value provider for citations. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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

from typing import Callable

from .items import Item
from .itemmapper import ItemGetValueContext, ItemType, ItemValueProvider
from .content import list_terms
from .contenttext import TextContent, TextMapper, latex_escape

_Fields = dict[str, str | list[str]]
_GetFields = Callable[[Item], tuple[str, _Fields]]

_FIELDS = {
    "author", "booktitle", "chapter", "doi", "edition", "editor",
    "howpublished", "institution", "journal", "month", "note", "number",
    "organization", "pages", "publisher", "school", "series", "title",
    "volume", "year"
}

_NO_LATEX_ESCAPE = {"url"}

_DOUBLE_QUOTE = {
    "author", "booktitle", "editor", "howpublished", "institution",
    "organization", "publisher", "school", "title"
}

_PERSONS = {"author", "editor"}


def _get_fields(item: Item) -> tuple[str, _Fields]:
    _, _, publication_type = item.type.partition("/")
    fields: _Fields = dict(
        (key, item[key]) for key in _FIELDS.intersection(item.data.keys()))
    url = item.get("work-url", None)
    if url is not None:
        fields["url"] = url
    return publication_type, fields


class BibTeXCitationProvider(ItemValueProvider):
    """ Provides citation values and BibTeX entries. """

    def __init__(self, mapper: TextMapper) -> None:
        super().__init__(mapper)
        self._citations: set[Item] = set()
        self._get_fields: dict[str, _GetFields] = {}
        mapper.add_get_value("reference:/cite", self._get_cite)
        mapper.add_get_value("reference:/cite-long", self._get_cite_long)

    def reset(self) -> None:
        self._citations.clear()

    def get_cite_group(self, ctx: ItemGetValueContext) -> str:
        """
        Get the citations associated with the citation group key provided by
        the arguments of the context.
        """
        citations: list[str] = []
        for link in ctx.item.links_to_children("citation-group-member"):
            if link["citation-group-key"] == ctx.args:
                citations.append(f"${{{link.uid}:/cite}}")
        return ctx.substitute(list_terms(citations))

    def get_bibtex_entries(self, ctx: ItemGetValueContext) -> str:
        """ Get the BibTeX entries for the collected citations. """
        mapper = ctx.mapper
        assert isinstance(mapper, TextMapper)
        content = mapper.create_content()
        self.add_bibtex_entries(content)
        return content.join()

    def _add_get_fields_for_subtypes(self, spec_type: ItemType, type_path: str,
                                     get_fields: _GetFields) -> None:
        if spec_type.refinements:
            for key, refinement in spec_type.refinements.items():
                self._add_get_fields_for_subtypes(refinement,
                                                  f"{type_path}/{key}",
                                                  get_fields)
        else:
            self._get_fields[type_path] = get_fields

    def add_get_fields(self, item_type: str, get_fields: _GetFields) -> None:
        """ Add the get fields method for the item type. """
        self.mapper.add_get_value(f"{item_type}:/cite", self._get_cite)
        self.mapper.add_get_value(f"{item_type}:/cite-long",
                                  self._get_cite_long)
        spec_type = self.mapper.item.cache.type_provider.root_type
        for name in item_type.split("/"):
            spec_type = spec_type.refinements[name]
        self._add_get_fields_for_subtypes(spec_type, item_type, get_fields)

    def add_bibtex_entries(self, content: TextContent) -> None:
        """ Add BibTeX entries for the collected citations to the content. """
        for item in sorted(self._citations):
            publication_type, fields = self._get_fields.get(
                item.type, _get_fields)(item)
            for key in _PERSONS.intersection(fields.keys()):
                if isinstance(fields[key], list):
                    fields[key] = " and ".join(fields[key])
            content.append(f"@{publication_type}{{{item.ident},")
            for field, value in sorted(fields.items()):
                assert isinstance(value, str)
                value = self.mapper.substitute(value)
                if field not in _NO_LATEX_ESCAPE:
                    value = latex_escape(value)
                if field in _DOUBLE_QUOTE:
                    value = f"{{{value}}}"
                content.append(f"  {field} = {{{value}}},")
            content.append("}")

    def _get_cite(self, ctx: ItemGetValueContext) -> str:
        self._citations.add(ctx.item)
        assert isinstance(self.mapper, TextMapper)
        content = self.mapper.create_content()
        return content.cite(ctx.item.ident)

    def _get_cite_long(self, ctx: ItemGetValueContext) -> str:
        self._citations.add(ctx.item)
        _, fields = self._get_fields.get(ctx.item.type, _get_fields)(ctx.item)
        assert isinstance(self.mapper, TextMapper)
        content = self.mapper.create_content()
        title = fields["title"]
        assert isinstance(title, str)
        title = content.emphasize(ctx.substitute_and_transform(title))
        return f"{title} {content.cite(ctx.item.ident)}"
