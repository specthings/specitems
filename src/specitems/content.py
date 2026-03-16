# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for content generation. """

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

import abc
from contextlib import contextmanager
import dataclasses
import collections
import itertools
import os
import re
import textwrap
from typing import (Callable, ContextManager, Deque, Iterable, Iterator,
                    Optional, Sequence, Union)

from .items import Item
from .itemmapper import ItemGetValueContext

ContentAddContext = Callable[["Content"], ContextManager[None]]
GenericContent = Union[str, list[str], "Content"]
GenericContentIterable = Union[Iterable[str], Iterable[list[str]],
                               Iterable[GenericContent]]

MARKDOWN_ROLES = re.compile(r"\{([^}]+)\}`([^`]+)`", flags=re.DOTALL)


def split_copyright_statement(statement: str) -> tuple[str, set[int]]:
    """ Split the copyright statement into the holder and year set. """
    match = re.search(
        r"^\s*Copyright\s+\(C\)\s+([0-9]+),\s*([0-9]+)\s+(.+)\s*$",
        statement,
        flags=re.I,
    )
    if match:
        return match.group(3), set((int(match.group(1)), int(match.group(2))))
    match = re.search(
        r"^\s*Copyright\s+\(C\)\s+([0-9]+)\s+(.+)\s*$",
        statement,
        flags=re.I,
    )
    if match:
        return match.group(2), set((int(match.group(1)), ))
    raise ValueError(statement)


def make_copyright_statement(holder: str,
                             years: set[int],
                             line: str = "Copyright (C)") -> str:
    """ Make the copyright statement from the holder and year set. """
    year_count = len(years)
    line += f" {min(years)}"
    if year_count > 1:
        line += f", {max(years)}"
    line += f" {holder}"
    return line


def list_terms(terms: Sequence[str], conjunction: str = "and") -> str:
    """
    List the terms.  While there are two terms or more, the conjunction will
    be placed before the last term.  While there are three terms or more, a
    serial comma will be placed before the conjunction.
    """
    count = len(terms)
    if count == 0:
        return ""
    if count == 1:
        return terms[0]
    if count == 2:
        return f"{terms[0]} {conjunction} {terms[1]}"
    return f"{', '.join(terms[:-1])}, {conjunction} {terms[-1]}"


class Copyright:
    """
    Represents a copyright holder with its years of substantial contributions.
    """

    @classmethod
    def from_statement(cls, statement: str) -> "Copyright":
        """ Make a copyright from the statement. """
        holder, years = split_copyright_statement(statement)
        return Copyright(holder, years)

    def __init__(self, holder: str, years: Optional[set[int]] = None):
        self.holder = holder
        self.years = years if years is not None else set()

    def add_year(self, year: int):
        """
        Add the year to the set of substantial contributions of this copyright
        holder.
        """
        self.years.add(year)

    def get_statement(self, line: str = "Copyright (C)") -> str:
        """ Return the associated copyright statement. """
        return make_copyright_statement(self.holder, self.years, line)

    def __lt__(self, other: "Copyright") -> bool:
        return (min(self.years), max(self.years),
                other.holder) < (min(other.years), max(other.years),
                                 self.holder)


def _copyright_key(holder_years):
    return (-min(holder_years[1]), -max(holder_years[1]), holder_years[0])


class Copyrights(dict):
    """ Represents a set of copyright holders. """

    def register(self, statements: Union[str, Iterable[str]]) -> None:
        """ Register the copyright statement. """
        if isinstance(statements, str):
            statements = [statements]
        for statement in statements:
            holder, years = split_copyright_statement(statement)
            self.setdefault(holder, set()).update(years)

    def get_statements(self, line: str = "Copyright (C)") -> list[str]:
        """ Return all registered copyright statements as a sorted list. """
        return [
            make_copyright_statement(holder, years, line)
            for holder, years in sorted(self.items(), key=_copyright_key)
        ]


def make_lines(content: Optional[GenericContent]) -> list[str]:
    """ Make a list of lines from the generic content. """
    # pylint: disable=protected-access
    if isinstance(content, str):
        return content.strip("\n").split("\n")
    if isinstance(content, list):
        return content
    if content is None:
        return []
    return content._lines


def make_text(content: Optional[GenericContent]) -> str:
    """ Make a text from the generic content. """
    # pylint: disable=protected-access
    if isinstance(content, str):
        return content.strip("\n")
    if isinstance(content, list):
        return "\n".join(content)
    if content is None:
        return ""
    return "\n".join(content._lines)


@contextmanager
def _add_context(_content: "Content") -> Iterator[None]:
    yield


def _empty_line_indent(indents: list[str]) -> str:
    indent = "".join(indents)
    if indent.isspace():
        return ""
    return indent


_SPECIAL_BLOCK = re.compile(r"( *[-*] | *[0-9]+\. | +)")

_DIRECTIVE_BEGIN = re.compile(r"(```+)(.*)")


@dataclasses.dataclass
class _LineContext:
    begin_index: int
    content_begin_index: int
    content_end_index: int
    last_line: str | None
    last_is_not_empty: bool

    def content_begin(self, content: "Content") -> None:
        """ Set the content begin context. """
        self.content_begin_index = len(content)


class Content(abc.ABC):
    """
    Builds content.

    While the gap property is true, the add() method shall add a gap before the
    added content, otherwise no gap shall be added.
    """
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    AUTOMATICALLY_GENERATED_WARNING = [
        "This file was automatically generated.  Do not edit it."
    ]

    def __init__(self, the_license: str | set[str] | None):
        self.gap = False
        self.text_width = 79
        self.copyrights = Copyrights()
        self._lines: list[str] = []
        if the_license is None:
            the_license = {"CC-BY-SA-4.0"}
        elif isinstance(the_license, str):
            the_license = {the_license}
        self._license = the_license
        self._tab = "  "
        self._is_initial_indents: list[bool] = [False]
        self._indents = [""]
        self._initial_indents = [[""]]
        self._subsequent_indents = [""]
        self._empty_line_indents = [""]
        self._line_indent = ""
        self._empty_line_indent = ""
        self._last_line: str | None = None
        self._last_is_initial_indent = True
        self._last_is_not_empty = False
        self._pop_indent_gap = False
        self._comment_prefix = "#"
        self._line_contexts: list[_LineContext] = []

    def __iter__(self):
        yield from self._lines

    def __bool__(self):
        return bool(self._lines)

    def __len__(self):
        return len(self._lines)

    def __str__(self):
        return "\n".join(itertools.chain(self._lines, [""]))

    def join(self, linesep: str = "\n") -> str:
        """ Join the lines using the line separator to a string. """
        return linesep.join(self._lines)

    @property
    def tab(self) -> str:
        """ The tabulator. """
        return self._tab

    @property
    def licenses(self) -> str:
        """ The licenses of the content in SPDX format. """
        return " OR ".join(sorted(self._license))

    @property
    def last(self) -> str:
        """ Is the last line. """
        return self._lines[-1]

    @last.setter
    def last(self, line: str) -> None:
        self._lines[-1] = line

    def is_at_empty_list_item(self) -> bool:
        """
        Returns true, if the content end is at an empty list item, otherwise
        false.
        """
        return self._is_initial_indents[-1] and self._indents[-1] == "- "

    def _indent(self, lines: list[str], gap: bool) -> None:
        if not lines:
            return
        self._last_line = lines[-1]
        last_is_not_empty = self._last_is_not_empty
        self._last_is_not_empty = bool(lines[-1])
        indent = self._line_indent
        if self._is_initial_indents[-1]:
            self._lines.append(f"{indent}{lines[0]}")
            self._last_is_initial_indent = True
            self._is_initial_indents = [
                False for _ in self._is_initial_indents
            ]
            self._indents = self._subsequent_indents.copy()
            indent = "".join(self._indents)
            self._line_indent = indent
            lines = lines[1:]
            gap = False
        if lines:
            empty = self._empty_line_indent
            if gap and last_is_not_empty:
                self._lines.append(empty)
            self._last_is_initial_indent = False
            self._lines.extend(f"{indent if line_2 else empty}{line_2}"
                               for line_2 in lines)

    def append(self, content: Optional[GenericContent]) -> None:
        """ Append the content. """
        self._indent(make_lines(content), False)
        self.gap = True

    def prepend(self, content: Optional[GenericContent]) -> None:
        """ Prepend the content. """
        self._lines[0:0] = make_lines(content)

    def add(self,
            content: Optional[GenericContent],
            context: ContentAddContext = _add_context) -> None:
        """
        Skip leading empty lines, add a gap if needed, then add the content.
        """
        if not content:
            return
        lines = make_lines(content)
        for index, line in enumerate(lines):
            if line:
                with context(self):
                    self._indent(lines[index:], self.gap)
                    self.gap = True
                break

    def _add_verbatim(self, prefix: str, block: str,
                      blocks: Deque[str]) -> None:
        gap = False
        while True:
            if block.endswith(prefix):
                block = block[:-len(prefix)]
                if block:
                    self.add(block)
                    self.gap = False
                else:
                    self.gap = gap
                self.add_directive_end(prefix)
                break
            self.add(block)
            if not blocks:
                break
            block = blocks.popleft()
            gap = True

    def convert(self, text: str) -> str:
        """ Convert the text in Markdown format to the content format """
        return text

    def add_directive_begin(self, prefix: str, directive: str) -> None:
        """ Add the directive begin. """
        self.add(f"{prefix}{directive}")
        self.gap = False

    def add_directive_end(self, prefix: str) -> None:
        """ Add the directive end. """
        self.add(prefix)

    def wrap_text(self,
                  text: str,
                  initial_indent: str = "",
                  subsequent_indent: Optional[str] = None,
                  context: ContentAddContext = _add_context) -> None:
        """ Add a gap if needed, then add the wrapped text.  """
        with context(self):
            if subsequent_indent is None:
                if initial_indent:
                    subsequent_indent = self._tab
                else:
                    subsequent_indent = ""
            wrapper = textwrap.TextWrapper()
            wrapper.break_long_words = False
            wrapper.break_on_hyphens = False
            wrapper.width = self.text_width - len(self._line_indent)
            blocks = collections.deque(text.split("\n\n"))
            while blocks:
                block = blocks.popleft()
                mobj = _DIRECTIVE_BEGIN.match(block)
                if mobj:
                    self.add_directive_begin(mobj.group(1), mobj.group(2))
                    self._add_verbatim(mobj.group(1),
                                       block[len(mobj.group(0)) + 1:], blocks)
                    self.gap = True
                    continue
                mobj = _SPECIAL_BLOCK.match(block)
                if mobj:
                    length = len(mobj.group(0))
                    space = length * " "
                    wrapper.initial_indent = f"{initial_indent}{mobj.group(0)}"
                    wrapper.subsequent_indent = f"{subsequent_indent}{space}"
                    block = block[length:].replace(f"\n{space}", "\n")
                else:
                    wrapper.initial_indent = initial_indent
                    wrapper.subsequent_indent = subsequent_indent
                block = self.convert(block)
                self._indent(wrapper.wrap(block), self.gap)
                self.gap = True
                initial_indent = subsequent_indent

    def wrap(self,
             content: Optional[GenericContent],
             initial_indent: str = "",
             subsequent_indent: Optional[str] = None,
             context: ContentAddContext = _add_context) -> None:
        """ Add a gap if needed, then add the wrapped content.  """
        text = make_text(content).strip()
        if not text:
            return
        self.wrap_text(text, initial_indent, subsequent_indent, context)

    def paste(self, content: Optional[GenericContent]) -> None:
        """ Paste the wrapped content directly to the last line.  """
        text = make_text(content).strip()
        if not text:
            return
        last_line = self._last_line
        if not last_line:
            self.wrap_text(text)
            return
        self._is_initial_indents[-1] = self._last_is_initial_indent
        if self._last_is_initial_indent:
            self._indents = self._initial_indents[-1].copy()
        else:
            self._indents = self._subsequent_indents.copy()
        self._line_indent = "".join(self._indents)
        self._lines.pop()
        self.gap = False
        self.wrap_text(f"{last_line.rstrip()} {text}")

    def set_pop_indent_gap(self, pop_indent_gap: bool) -> None:
        """ Set the gap indicator used after popping an indentation. """
        self._pop_indent_gap = pop_indent_gap

    def push_indent(self,
                    initial_indent: Optional[str] = None,
                    subsequent_indent: Optional[str] = None,
                    empty_line_indent: Optional[str] = None) -> None:
        """ Push the indentation level. """
        if initial_indent is None:
            initial_indent = self._tab
        if subsequent_indent is None:
            subsequent_indent = initial_indent
        if empty_line_indent is None:
            empty_line_indent = self._tab
        self._is_initial_indents.append(True)
        self._indents.append(initial_indent)
        self._initial_indents.append(self._indents.copy())
        self._subsequent_indents.append(subsequent_indent)
        self._empty_line_indents.append(empty_line_indent)
        self._line_indent = "".join(self._indents)
        self._empty_line_indent = _empty_line_indent(self._empty_line_indents)
        self._last_line = None
        self.gap = False

    def pop_indent(self) -> None:
        """ Pop the indentation level. """
        self._is_initial_indents.pop()
        self._indents.pop()
        self._initial_indents.pop()
        self._subsequent_indents.pop()
        self._empty_line_indents.pop()
        self._line_indent = "".join(self._indents)
        self._empty_line_indent = _empty_line_indent(self._empty_line_indents)
        self._last_line = None
        self.gap = self._pop_indent_gap

    @contextmanager
    def indent(self,
               initial_indent: Optional[str] = None,
               subsequent_indent: Optional[str] = None,
               empty_line_indent: Optional[str] = None,
               levels: int = 1) -> Iterator[None]:
        """ Open an indentation context. """
        for _ in range(levels):
            self.push_indent(initial_indent, subsequent_indent,
                             empty_line_indent)
        yield
        for _ in range(levels):
            self.pop_indent()

    def indent_lines(self, level: int) -> None:
        """ Indent all lines by the specified indentation level. """
        prefix = level * self._tab
        self._lines = [prefix + line if line else line for line in self._lines]

    def push_line_context(self) -> _LineContext:
        """
        Initialize a line context, push it to the line context stack, and
        return it.
        """
        line_context = _LineContext(len(self._lines), 0, -1, self._last_line,
                                    self._last_is_not_empty)
        self._line_contexts.append(line_context)
        return line_context

    def pop_line_context(self) -> _LineContext:
        """
        Pop the last element from the line context stack and set the content
        end of the line context.
        """
        line_context = self._line_contexts.pop()
        line_context.content_end_index = len(self._lines)
        return line_context

    def check_line_context(self, line_context: _LineContext) -> None:
        """
        Check the line context and restore the line state if necessary.
        """
        if line_context.content_begin_index == line_context.content_end_index:
            self._last_line = line_context.last_line
            self._last_is_not_empty = line_context.last_is_not_empty
            self._lines = self._lines[0:line_context.begin_index]

    def add_blank_line(self):
        """ Add a blank line. """
        self._indent([""], False)

    def ensure_blank_line(self):
        """ Ensure that the last line is blank. """
        if self._last_is_not_empty:
            self.add_blank_line()

    def register_license(self, the_license: str) -> None:
        """ Register the licence for the content. """
        licenses = set(re.split(r"\s+OR\s+", the_license))
        if not self._license.intersection(licenses):
            raise ValueError(
                f"no overlap of {sorted(self._license)} and {sorted(licenses)}"
            )

    def register_copyright(self, statement: str) -> None:
        """ Register the copyright statement for the content. """
        self.copyrights.register(statement)

    def register_license_and_copyrights_of_item(self, item: Item) -> None:
        """ Register the license and copyrights of the item. """
        try:
            self.register_license(item["SPDX-License-Identifier"])
        except ValueError as err:
            raise ValueError(f"for item {item.uid}: {err}") from err
        for statement in item["copyrights"]:
            self.register_copyright(statement)

    def set_comment_prefix(self, comment_prefix: str) -> None:
        """ Set the comment prefix. """
        self._comment_prefix = comment_prefix

    def open_comment_block(self) -> None:
        """ Open a comment block. """
        if self.gap:
            self.ensure_blank_line()
        prefix = f"{self._comment_prefix} "
        self.push_indent(prefix, prefix, self._comment_prefix)

    def close_comment_block(self) -> None:
        """ Close the comment block. """
        self.pop_indent()
        self.gap = True

    @contextmanager
    def comment_block(self) -> Iterator[None]:
        """ Open a comment block context. """
        self.open_comment_block()
        yield
        self.close_comment_block()

    def add_list_item(self, content: GenericContent) -> None:
        """ Add the list item. """
        self.ensure_blank_line()
        with self.indent("- ", "  "):
            self.wrap(content)

    def add_list(self,
                 items: GenericContentIterable,
                 prologue: Optional[GenericContent] = None,
                 epilogue: Optional[GenericContent] = None,
                 empty: Optional[GenericContent] = None) -> None:
        """
        Add the list with prologue and epilogue or the empty list statement.
        """
        if items:
            self.wrap(prologue)
            for item in items:
                self.add_list_item(item)
            self.wrap(epilogue)
        else:
            self.wrap(empty)

    def open_list_item(self, content: GenericContent) -> None:
        """ Open a list item. """
        self.ensure_blank_line()
        self.push_indent("- ", "  ", "")
        self.wrap(content)

    def close_list_item(self) -> None:
        """ Close the list item. """
        self.pop_indent()
        self.gap = True

    @contextmanager
    def list_item(self, content: GenericContent) -> Iterator[None]:
        """ Open a list item context. """
        self.open_list_item(content)
        yield
        self.close_list_item()

    def add_automatically_generated_warning(self) -> None:
        """ Add a warning that the file is automatically generated. """
        with self.comment_block():
            self.append(Content.AUTOMATICALLY_GENERATED_WARNING)

    def beautify(self) -> str:
        """ Return the beautified content. """
        return str(self)

    def write(self, path: str, beautify: bool = False) -> None:
        """ Write the content to the file specified by the path. """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        if beautify:
            text = self.beautify()
        else:
            text = str(self)
        with open(path, "w+", encoding="utf-8") as out:
            out.write(text)


def get_value_plural(ctx: ItemGetValueContext) -> str:
    """ Get the value as a glossary term plural. """
    try:
        return ctx.value[ctx.key]
    except KeyError:
        term = ctx.value["term"]
        if term.endswith("y"):
            return f"{term[:-1]}ies"
        return f"{term}s"


_CAMEL_CASE_TO_UPPER = re.compile(r"\s+(.)")
_CAMEL_CASE_DISCARD = re.compile(r"[^ \t\n\r\f\va-zA-Z0-9]")


def to_camel_case(name: str) -> str:
    """ Return the name in CamelCase. """
    name = _CAMEL_CASE_TO_UPPER.sub(
        lambda match: match.group(1).upper(),
        _CAMEL_CASE_DISCARD.sub(" ", name.replace("+", "X")))
    return f"{name[0].upper()}{name[1:]}"
