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

import dataclasses
import re
from typing import Callable, Optional

from .items import Item, Link
from .itemmapper import ItemGetValueContext, ItemType, ItemValueProvider
from .content import list_terms
from .contenttext import TextContent, TextMapper, latex_escape

_Fields = dict[str, str | list[str]]
_GetFields = Callable[[Item], tuple[str, _Fields]]

_FIELDS = {
    "author", "booktitle", "chapter", "date", "doi", "edition", "editor",
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

_NOT_ID_CHARS = re.compile(r"[^a-z0-9]+")


def make_anchor(label: str) -> str:
    """
    Make the anchor of the label in the way Sphinx makes the identifier of a
    label target.
    """
    return _NOT_ID_CHARS.sub("-", label.lower()).strip("-")


@dataclasses.dataclass
class ReferenceTarget:
    """ Represents the target of a reference link. """

    # pylint: disable=too-many-instance-attributes

    #: The referenced work.
    work: Item

    #: The name of the area within the work.
    name: Optional[str]

    #: The label of the area within the work.
    label: Optional[str]

    #: The location of the area within the work.
    location: Optional[str]

    #: The path of the area relative to the base URL of the work.
    path: str

    #: The anchor of the area within the page of the work.
    anchor: Optional[str]

    #: The URL of the area.  The caller substitutes it in the context of the
    #: work.
    url: Optional[str]


def get_reference_work(item: Item) -> Item:
    """
    Get the referenced work of the reference or reference location item.
    """
    if item.type == "reference-location":
        works = list(item.parents("reference-location"))
        if len(works) != 1:
            raise ValueError(f"{item.uid}: a reference location shall have "
                             "exactly one link to the referenced work")
        return works[0]
    return item


def get_reference_target(item: Item,
                         link: Optional[Link] = None) -> ReferenceTarget:
    """
    Get the target of the reference or reference location item.

    The attributes of the optional reference link take precedence over the
    attributes of the reference location.  The paths of the reference location
    and the reference link are concatenated.  The anchor comes from the first
    of the reference link and the reference location which has an anchor or a
    label.  An anchor attribute gives the anchor, otherwise the label yields
    it.
    """
    work = get_reference_work(item)
    link_data = {} if link is None else link.data
    area = item.data if item is not work else {}
    name = area.get("name")
    label = link_data.get("label", area.get("label"))
    location = link_data.get("location", area.get("location"))
    path = f"{area.get('path', '')}{link_data.get('path', '')}"
    anchor: Optional[str] = None
    for data in (link_data, area):
        if "anchor" in data:
            anchor = data["anchor"]
            break
        if "label" in data:
            anchor = make_anchor(data["label"])
            break
    base = work.get("work-base-url")
    url: Optional[str] = None
    if base is not None:
        fragment = "" if anchor is None else f"#{anchor}"
        url = f"{base}{path}{fragment}"
    return ReferenceTarget(work, name, label, location, path, anchor, url)


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
        mapper.add_get_value("reference-location:/cite",
                             self._get_cite_location)
        mapper.add_get_value("reference-location:/cite-long",
                             self._get_cite_long_location)

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

    def get_fields(self, item: Item) -> tuple[str, _Fields]:
        """ Get the BibTeX type and fields of the item. """
        return self._get_fields.get(item.type, _get_fields)(item)

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
            publication_type, fields = self.get_fields(item)
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

    def _cite(self, work: Item) -> str:
        self._citations.add(work)
        assert isinstance(self.mapper, TextMapper)
        content = self.mapper.create_content()
        return content.cite(work.ident)

    def _cite_long(self, ctx: ItemGetValueContext, work: Item,
                   name: Optional[str]) -> str:
        _, fields = self.get_fields(work)
        assert isinstance(self.mapper, TextMapper)
        content = self.mapper.create_content()
        title = fields["title"]
        assert isinstance(title, str)
        if work is ctx.item:
            title = ctx.substitute(title)
        else:
            title = self.mapper.substitute_data(title, work)
        title = content.emphasize(ctx.transform(title))
        if name is not None:
            title = f"{title}, {ctx.substitute_and_transform(name)}"
        return f"{title} {self._cite(work)}"

    def _get_cite(self, ctx: ItemGetValueContext) -> str:
        return self._cite(ctx.item)

    def _get_cite_long(self, ctx: ItemGetValueContext) -> str:
        return self._cite_long(ctx, ctx.item, None)

    def _get_cite_location(self, ctx: ItemGetValueContext) -> str:
        return self._cite(get_reference_work(ctx.item))

    def _get_cite_long_location(self, ctx: ItemGetValueContext) -> str:
        return self._cite_long(ctx, get_reference_work(ctx.item),
                               ctx.item.get("name"))
