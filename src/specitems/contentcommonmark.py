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

import collections
from typing import Iterable, Optional, Sequence

from .content import GenericContent, make_lines
from .contentmarkdown import MarkdownContent
from .contenttext import COL_SPAN, ROW_SPAN, TextContent, TextMapper


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
        # pylint: disable=too-many-locals
        if not rows:
            return
        lines: collections.deque[str] = collections.deque()
        lines.appendleft("</table>")
        row_span: list[int] = [1] * len(list(rows[0]))
        header_index = len(rows) - header_rows
        for row_index, row in enumerate(reversed(rows)):
            if row_index < header_index:
                cell_type = "td"
            else:
                cell_type = "th"
            col_span = 1
            line = "</tr>"
            for col_index, cell in enumerate(reversed(tuple(row))):
                if isinstance(cell, str):
                    cell_start = f"<{cell_type}"
                    if row_span[col_index] > 1:
                        cell_start = (f"{cell_start} "
                                      f"rowspan=\"{row_span[col_index]}\"")
                        row_span[col_index + 1 - col_span:col_index +
                                 1] = [1] * col_span
                    if col_span > 1:
                        cell_start = f"{cell_start} colspan=\"{col_span}\""
                        col_span = 1
                    line = f"{cell_start}>{cell}</{cell_type}>{line}"
                elif cell == COL_SPAN | ROW_SPAN:
                    col_span += 1
                    row_span[col_index] += 1
                elif cell == COL_SPAN:
                    col_span += 1
                else:
                    row_span[col_index] += 1
            lines.appendleft(f"  <tr>{line}")
        lines.appendleft("<table>")
        self.append(list(lines))

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
