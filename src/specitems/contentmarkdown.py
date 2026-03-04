# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for MyST Markdown content generation. """

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

import re
from typing import Match, Optional

import mdformat

from .content import GenericContent, make_lines
from .contenttext import TextContent, TextMapper

_MDFORMAT_EXTENSIONS = {"deflist", "footnote", "frontmatter", "myst", "tables"}

_MDFORMAT_OPTIONS = {"end_of_line": "lf", "number": True, "wrap": 79}

_MDFORMAT_TERM_OPTIONS = {"end_of_line": "lf", "number": True, "wrap": 77}

_MD_SPECIAL_CHAR = re.compile(r"[\\\$\][*<_`]")


def _md_escape(match: Match) -> str:
    return f"\\{match.group(0)}"


class MarkdownContent(TextContent):
    """ This class builds MyST Markdown content. """

    def __init__(self,
                 section_level: int = 1,
                 the_license: str | set[str] | None = None):
        super().__init__(section_level, the_license)
        self.set_pop_indent_gap(True)
        self.set_comment_prefix("%")

    def get_reference(self, label: str, name: Optional[str] = None) -> str:
        if name:
            return f"{{ref}}`{name} <{label}>`"
        return f"{{ref}}`{label}`"

    def code(self, text: str) -> str:
        return f"`{text}`"

    def emphasize(self, text: str) -> str:
        return f"_{text}_"

    def strong(self, text: str) -> str:
        return f"*{text}*"

    def path(self, text: str) -> str:
        return f"`{text}`"

    def term(self, text: str, term: str | None = None) -> str:
        if term is None or term == text:
            return f"{{term}}`{text}`"
        return f"{{term}}`{text} <{term}>`"

    def cite(self, identifier: str) -> str:
        return f"{{cite}}`{identifier}`"

    def escape(self, text: str) -> str:
        return _MD_SPECIAL_CHAR.sub(_md_escape, text)

    def add_header(self, name, level=1, label=None) -> None:
        if label is not None:
            self.add(f"({label.strip()})=")
        self.add([f"{level * '#'} {name.strip()}", ""])

    def add_index_entries(self, entries: list[str]) -> None:
        for entry in entries:
            self.add([f"```{{index}} {entry}", "```"])

    def open_directive(self,
                       name: str,
                       value: Optional[str] = None,
                       options: Optional[list[str]] = None) -> None:
        if value is None:
            value = ""
        else:
            value = f" {value}"
        self.add(f"```{{{name.strip()}}}{value}")
        if options is not None:
            self.append(options)
        self.gap = False

    def close_directive(self) -> None:
        self.append("```")

    def add_rubric(self, name: str) -> None:
        self.add(["```{eval-rst}", f".. rubric:: {name}", "```", ""])

    def add_definition_item(self, name: GenericContent,
                            definition: GenericContent) -> None:
        self.add(name)
        lines = make_lines(definition)
        self.append(f": {lines[0]}")
        with self.indent("  "):
            self.append(lines[1:])

    def add_glossary_term(self, term: str, definition: str) -> None:
        self.add([term, ""])
        with self.indent("  "):
            self.append(
                mdformat.text(definition, options=_MDFORMAT_TERM_OPTIONS))

    def beautify(self) -> str:
        return mdformat.text(str(self),
                             options=_MDFORMAT_OPTIONS,
                             extensions=_MDFORMAT_EXTENSIONS)


class MarkdownMapper(TextMapper):
    """ Provides an item mapper for Markdown formatted text production. """

    def create_content(
            self,
            section_level: int = 0,
            the_license: str | set[str] | None = None) -> TextContent:
        return MarkdownContent(section_level, the_license)
