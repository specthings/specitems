# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for CommonMark content generation. """

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

from typing import Iterable, Optional, Sequence

from .content import GenericContent, make_lines
from .contentmarkdown import MarkdownContent
from .contenttext import COL_SPAN, ROW_SPAN, TextContent, TextMapper


def _make_simple(cell: str | int) -> str:
    if isinstance(cell, str):
        return cell
    if cell == ROW_SPAN | COL_SPAN:
        return "↖"
    if cell == COL_SPAN:
        return "←"
    return "↑"


class CommonMarkContent(MarkdownContent):
    """ This class builds CommonMark content. """

    def reference(self, label: str, name: Optional[str] = None) -> str:
        if not name:
            name = label
        return self.link(name, f"#{label}")

    def term(self, text: str, term: str | None = None) -> str:
        return text

    def cite(self, identifier: str) -> str:
        return ""

    def add_label(self, label: str) -> None:
        self.add(f"<a id=\"{label.strip()}\"></a>")

    def add_rubric(self, name: str) -> None:
        self.add([self.strong(name), ""])

    def add_image(self, base: str, width: Optional[str] = None) -> None:
        self.add(f"![]({base})")

    def add_index_entries(self, entries: list[str]) -> None:
        pass

    def open_directive(self,
                       name: str,
                       value: Optional[str] = None,
                       options: Optional[list[str]] = None) -> None:
        self.add(f"```{name.strip()}")
        self.gap = False

    def add_simple_table(self,
                         rows: Sequence[Iterable[str]],
                         widths: Optional[list[int]] = None,
                         font_size: Optional[str | int] = None) -> None:
        super().add_simple_table(rows)

    def add_grid_table(self,
                       rows: Sequence[Iterable[str | int]],
                       widths: Optional[list[int]] = None,
                       header_rows: int = 1,
                       font_size: Optional[str | int] = None) -> None:
        if not rows:
            return
        simple_rows = [
            tuple(_make_simple(cell) for cell in row) for row in rows
        ]
        self.add_simple_table(simple_rows)

    def add_definition_item(self, name: GenericContent,
                            definition: GenericContent) -> None:
        self.add(f"{self.strong(', '.join(make_lines(name)))}:")
        self.append(definition)

    def add_glossary_term(self, term: str, definition: str) -> None:
        self.add_definition_item(term, definition)

    def add_code_block(self,
                       code: list[str],
                       language: str = "none",
                       font_size: str | int = "footnotesize",
                       line_number_start: int = 1) -> None:
        with self.directive(language):
            self.append(code)


class CommonMarkMapper(TextMapper):
    """ Provides an item mapper for CommonMark formatted text production. """

    def create_content(
            self,
            section_level: int = 0,
            the_license: str | set[str] | None = None) -> TextContent:
        return CommonMarkContent(section_level, the_license)
