# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for reST content generation. """

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

from contextlib import contextmanager
import re
from typing import Iterable, Iterator, Match, Optional, Sequence

from .content import Content, GenericContent, MARKDOWN_ROLES
from .contenttext import COL_SPAN, ROW_SPAN, TextContent, TextMapper

_MD_CODE = re.compile(r"(^|\s)`([^`]+)`(\s|$)", flags=re.DOTALL)
_MD_EMPHASIZE = re.compile(r"(^|\s)_([^_]+)_(\s|$)", flags=re.DOTALL)
_MD_STRONG = re.compile(r"(^|\s)\*([^*]+)\*(\s|$)", flags=re.DOTALL)
_MD_REF = re.compile(r"\[([^\]]+)\]\(([^)]+)\)", flags=re.DOTALL)

_REST_SPECIAL_CHAR = re.compile(r"[\\*_`]")

_HEADER_LEVELS = ["#", "*", "=", "-", "^", "\""]


def _rest_escape(match: Match) -> str:
    return f"\\{match.group(0)}"


def get_reference(label: str, name: Optional[str] = None) -> str:
    """ Return the reference to the specified label. """
    if name:
        return f":ref:`{name} <{label}>`"
    return f":ref:`{label}`"


def _simple_sep(maxi: Iterable[int]) -> str:
    return " ".join(f"{'=' * width}" for width in maxi)


def _simple_row(row: Iterable[str], maxi: Iterable[int]) -> str:
    line = " ".join(f"{cell:{width}}" for cell, width in zip(row, maxi))
    return line.rstrip()


def _cell_len(cell: str | int) -> int:
    return len(cell) if isinstance(cell, str) else 0


def _grid_sep(maxi: Iterable[int], sep: str) -> str:
    return f"+{sep}" + f"{sep}+{sep}".join(f"{sep * width}"
                                           for width in maxi) + f"{sep}+"


def _grid_row(row: Iterable[str | int], maxi: Iterable[int]) -> str:
    line = ""
    for cell, width in zip(row, maxi):
        if isinstance(cell, str):
            line = f"{line} | {cell:{width}}"
        elif (cell & ROW_SPAN) == 0:
            line = f"{line} | {' ' * width}"
        else:
            line = f"{line}   {' ' * width}"
    return f"|{line[2:]} |"


_BINARY_DATA = re.compile(r"[^\x09\x20-\x7e]")


def _escape_char(match: re.Match[str]) -> str:
    return f"\\x{ord(match.group(0)):02x}"


def escape_code_line(line: str) -> str:
    """ Escape binary data and enforce a maximum line width. """
    line = _BINARY_DATA.sub(_escape_char, line)
    if len(line) > 1000:
        line = line[:1000]
        index = line.rfind("\\")
        if index >= 996:
            line = line[:index]
        line = f"{line}[... more data not shown in report ...]"
    return "\u200b" + "\u200b".join(char for char in line)


def _role_to_rest(match: Match) -> str:
    return f":{match.group(1)}:`{match.group(2)}`"


def _code_to_rest(match: Match) -> str:
    return f"{match.group(1)}``{match.group(2)}``{match.group(3)}"


def _emphasize_to_rest(match: Match) -> str:
    return f"{match.group(1)}*{match.group(2)}*{match.group(3)}"


def _strong_to_rest(match: Match) -> str:
    return f"{match.group(1)}**{match.group(2)}**{match.group(3)}"


def _ref_to_rest(match: Match) -> str:
    return f"`{match.group(1)} <{match.group(2)}>`__"


class SphinxContent(TextContent):
    """ Builds reST content. """

    # pylint: disable=too-many-public-methods
    def __init__(self,
                 section_level: int = 0,
                 the_license: str | set[str] | None = None):
        super().__init__(section_level, the_license)
        self.set_pop_indent_gap(True)
        self.set_comment_prefix("..")
        self._tab = "    "

    def convert(self, text: str) -> str:
        return MARKDOWN_ROLES.sub(
            _role_to_rest,
            _MD_REF.sub(
                _ref_to_rest,
                _MD_CODE.sub(
                    _code_to_rest,
                    _MD_EMPHASIZE.sub(_emphasize_to_rest,
                                      _MD_STRONG.sub(_strong_to_rest, text)))))

    def add_directive_begin(self, prefix: str, directive: str) -> None:
        self.open_directive("code-block", directive)

    def add_directive_end(self, prefix: str) -> None:
        self.close_directive()

    def link(self, name: str, target: str) -> str:
        return f"`{name} <{target}>`__"

    def reference(self, label: str, name: Optional[str] = None) -> str:
        if name:
            return f":ref:`{name} <{label}>`"
        return f":ref:`{label}`"

    def code(self, text: str) -> str:
        return f"``{text}``"

    def emphasize(self, text: str) -> str:
        return f"*{text}*"

    def strong(self, text: str) -> str:
        return f"**{text}**"

    def path(self, text: str) -> str:
        for char in "/-_.":
            text = text.replace(char, f"{char}\u200b")
        return f":file:`{text}`"

    def term(self, text: str, term: str | None = None) -> str:
        if term is None or term == text:
            return f":term:`{text}`"
        return f":term:`{text} <{term}>`"

    def cite(self, identifier: str) -> str:
        return f":cite:`{identifier}`"

    def escape(self, text: str) -> str:
        return _REST_SPECIAL_CHAR.sub(_rest_escape, text)

    def add_label(self, label: str) -> None:
        self.add([".. _" + label.strip() + ":", ""])

    def add_header(self,
                   name: str,
                   level: int = 0,
                   label: Optional[str] = None) -> None:
        """ Add the header. """
        if label is not None:
            self.add_label(label)
        name = name.strip()
        self.add([name, _HEADER_LEVELS[level] * len(name), ""])

    def add_rubric(self, name: str) -> None:
        self.add([f".. rubric:: {name}", ""])

    def add_index_entries(self, entries: list[str]) -> None:
        self.add([f".. index:: {entry}" for entry in entries])

    def open_directive(self,
                       name: str,
                       value: Optional[str] = None,
                       options: Optional[list[str]] = None) -> None:
        self.ensure_blank_line()
        self.push_indent("", self._tab)
        value = f" {value}" if value else ""
        self.append(f".. {name.strip()}::{value}")
        self.append(options)
        self.add_blank_line()

    def close_directive(self) -> None:
        self.pop_indent()

    def add_definition_item(self, name: GenericContent,
                            definition: GenericContent) -> None:

        @contextmanager
        def _definition_item_context(content: Content) -> Iterator[None]:
            assert isinstance(content, Content)
            content.add(name)
            content.push_indent()
            yield
            content.pop_indent()

        self.wrap(definition, context=_definition_item_context)

    def add_glossary_term(self, term: str, definition: str) -> None:
        self.add_definition_item(term, definition)

    def _add_table(self, lines: list[str], widths: Optional[list[int]],
                   font_size: Optional[str | int]) -> None:
        options = [":class: longtable"]
        if widths:
            options.append(f":widths: {','.join(str(w) for w in widths)}")
        if font_size is not None:
            self.open_latex_font_size(font_size)
        with self.directive("table", options=options):
            self.add(lines)
        if font_size is not None:
            self.close_latex_font_size(font_size)

    def add_simple_table(self,
                         rows: Sequence[Iterable[str]],
                         widths: Optional[list[int]] = None,
                         font_size: Optional[str | int] = None) -> None:
        if not rows:
            return
        maxi = tuple(map(len, rows[0]))
        for row in rows:
            row_lengths = tuple(map(len, row))
            maxi = tuple(map(max, zip(maxi, row_lengths)))
        sep = _simple_sep(maxi)
        lines = [sep, _simple_row(rows[0], maxi), sep]
        lines.extend(_simple_row(row, maxi) for row in rows[1:])
        lines.append(sep)
        self._add_table(lines, widths, font_size)

    def add_grid_table(self,
                       rows: Sequence[Iterable[str | int]],
                       widths: Optional[list[int]] = None,
                       header_rows: int = 1,
                       font_size: Optional[str | int] = None) -> None:
        if not rows:
            return
        maxi = tuple(map(_cell_len, rows[0]))
        for row in rows:
            row_lengths = tuple(map(_cell_len, row))
            maxi = tuple(map(max, zip(maxi, row_lengths)))
        begin_end = _grid_sep(maxi, "-")
        lines = [begin_end]
        for index, row in enumerate(rows):
            if index > 0:
                sep = ""
                for cell, width in zip(row, maxi):
                    if isinstance(cell, str) or (cell & COL_SPAN) == 0:
                        if index == header_rows:
                            sep = f"{sep}+{'=' * (width + 2)}"
                        else:
                            sep = f"{sep}+{'-' * (width + 2)}"
                    elif (cell & ROW_SPAN) == 0:
                        sep = f"{sep}+{' ' * (width + 2)}"
                    else:
                        sep = f"{sep} {' ' * (width + 2)}"
                lines.append(f"{sep}+")
            lines.append(_grid_row(row, maxi))
        lines.append(begin_end)
        self._add_table(lines, widths, font_size)

    def add_code_block(self,
                       code: list[str],
                       language: str = "none",
                       font_size: str | int = "footnotesize",
                       line_number_start: int = 1) -> None:
        with self.latex_font_size(font_size):
            for index in range(0, len(code), 100):
                options: list[str] = []
                if line_number_start > 0:
                    options.extend([
                        ":linenos:",
                        f":lineno-start: {index + line_number_start}"
                    ])
                with self.directive("code-block",
                                    value=language,
                                    options=options):
                    line = code[index]
                    try:
                        first_char = line[0]
                    except IndexError:
                        line = "\u200b"
                    else:
                        if first_char.isspace():
                            line = f"\u200b{line}"
                    self.append(line)
                    self.append(code[index + 1:index + 100])

    def add_program_output(self,
                           output: list[str],
                           data_ranges: list[tuple[int, int]],
                           output_label: str | None = None,
                           font_size: str | int = "tiny") -> None:
        """ Add the program output. """
        with self.latex_font_size(font_size):
            end = len(output)
            data_ranges = data_ranges + [(end + 100, end + 100)]
            index = 0
            label = 0
            while index < end:
                if index >= label:
                    if output_label is not None:
                        self.add_label(f"{output_label}{label}")
                    label += 100
                options = [":linenos:", f":lineno-start: {index + 1}"]
                block_begin = index
                data_begin = data_ranges[0][0]
                if index <= data_begin < index + 100:
                    index = data_ranges[0][1]
                    data_ranges.pop(0)
                    block_end = data_begin
                    more = ["[... data lines not shown in report ...]"]
                else:
                    index += 100
                    block_end = index
                    more = []
                with self.directive("code-block", "none", options):
                    self.add([
                        escape_code_line(line)
                        for line in output[block_begin:block_end]
                    ] + more)


class SphinxMapper(TextMapper):
    """ Provides an item mapper for reST formatted text production. """

    def create_content(
            self,
            section_level: int = 0,
            the_license: str | set[str] | None = None) -> TextContent:
        return SphinxContent(section_level, the_license)
