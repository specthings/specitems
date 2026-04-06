# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for text content generation. """

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

import abc
import contextlib
from typing import Iterator, Optional

from .content import Content, GenericContent, get_value_plural, to_camel_case
from .items import Item
from .itemmapper import ItemGetValueContext, ItemMapper

_LATEX_SIZES = {
    -4: "tiny",
    -3: "scriptsize",
    -2: "footnotesize",
    -1: "small",
    0: "normalsize",
    1: "large",
    2: "Large",
    3: "LARGE",
    4: "huge",
    5: "Huge",
}


def _latex_font_size(size: str | int) -> str:
    if isinstance(size, str):
        return size
    return _LATEX_SIZES[max(min(size, 5), -4)]


def make_label(name: str) -> str:
    """ Return the label for the specified name. """
    return to_camel_case(name.strip())


def latex_escape(text: str) -> str:
    """ Escape the special LaTeX characters '_' and '&'.  """
    return text.replace("_", "\\_").replace("&", "\\&")


class TextContent(Content):
    """ Builds text content. """

    # pylint: disable=too-many-public-methods

    def __init__(self,
                 section_level: int = 0,
                 the_license: str | set[str] | None = None) -> None:
        super().__init__(the_license)
        self._section_level = section_level
        self._label_stack = [""]
        self._section_stack: list[str] = []

    def add_licence_and_copyrights(self) -> None:
        """
        Add a licence and copyright block according to the registered licenses
        and copyrights.
        """
        statements = self.copyrights.get_statements()
        if statements:
            self.prepend("")
            self.prepend(
                [f"{self._comment_prefix} {stm}" for stm in statements])
        self.prepend([
            f"{self._comment_prefix} SPDX-License-Identifier: {self.licenses}",
            ""
        ])

    @property
    def section_level(self) -> int:
        """ Get the section level of the current scope. """
        return self._section_level + len(self._section_stack)

    def get_sections(self) -> list[str]:
        """ Get the list of sections of the current scope. """
        return self._section_stack

    @property
    def label(self) -> str:
        """ This is the top of the label stack. """
        return self._label_stack[-1]

    def get_label(self, label_tail: str = "") -> str:
        """
        Return the concatenation of the top of the label stack and the label
        tail.
        """
        return f"{self.label}{label_tail}"

    def push_label(self, label: str) -> None:
        """ Push the label to the label stack. """
        self._label_stack.append(label)

    def push_label_tail(self, label_tail: str) -> str:
        """
        Make a label from the concatenation of the top of the label stack and
        the label tail.  Push this label to the label stack and returns it.
        """
        label = self.get_label(label_tail)
        self.push_label(label)
        return label

    def pop_label(self) -> None:
        """ Pop the top from the label stack. """
        self._label_stack.pop()

    @contextlib.contextmanager
    def label_scope(self, label: str) -> Iterator[None]:
        """ Open a label scope context. """
        self.push_label(label)
        yield
        self.pop_label()

    @abc.abstractmethod
    def get_reference(self, label: str, name: Optional[str] = None) -> str:
        """ Return the reference to the label with the optional name.  """

    @abc.abstractmethod
    def code(self, text: str) -> str:
        """ Return the text as formatted code. """

    @abc.abstractmethod
    def emphasize(self, text: str) -> str:
        """ Return the text formatted as emphasized text. """

    @abc.abstractmethod
    def strong(self, text: str) -> str:
        """ Return the text formatted as strong text. """

    @abc.abstractmethod
    def path(self, text: str) -> str:
        """ Return the text formatted as a path to a file or directory. """

    @abc.abstractmethod
    def term(self, text: str, term: str | None = None) -> str:
        """
        Return the text formatted as a glossary term.  If the term is
        specified and not equal to the text, then it will be used as the
        actually referenced term.
        """

    @abc.abstractmethod
    def cite(self, identifier: str) -> str:
        """ Return the identifier formatted as a citation reference. """

    @abc.abstractmethod
    def escape(self, text: str) -> str:
        """ Return the text with escaped special characters. """

    @abc.abstractmethod
    def add_label(self, label: str) -> None:
        """ Add the label. """

    @abc.abstractmethod
    def add_header(self,
                   name: str,
                   level: int = 0,
                   label: Optional[str] = None) -> None:
        """
        Add a header with the name at the level with the optional label.
        """

    @abc.abstractmethod
    def add_rubric(self, name: str) -> None:
        """ Add a rubric with the name. """

    @abc.abstractmethod
    def add_index_entries(self, entries: list[str]) -> None:
        """ Add the list of index entries. """

    def open_section(self,
                     name: str,
                     label_tail: Optional[str] = None,
                     label: Optional[str] = None) -> str:
        """ Open the section. """
        line_context = self.push_line_context()
        if label is None:
            if label_tail is None:
                label_tail = make_label(name)
            label = self.push_label_tail(label_tail)
        else:
            self.push_label(label)
        self.add_header(name, self.section_level, label)
        self._section_stack.append(name)
        line_context.content_begin(self)
        return label

    def close_section(self) -> None:
        """ Close the section. """
        line_context = self.pop_line_context()
        self._section_stack.pop()
        self.pop_label()
        self.check_line_context(line_context)

    @contextlib.contextmanager
    def section(self,
                name: str,
                label_tail: Optional[str] = None,
                label: Optional[str] = None) -> Iterator[str]:
        """ Open the section context. """
        yield self.open_section(name, label_tail, label)
        self.close_section()

    @abc.abstractmethod
    def open_directive(self,
                       name: str,
                       value: Optional[str] = None,
                       options: Optional[list[str]] = None) -> None:
        """ Open the directive. """

    @abc.abstractmethod
    def close_directive(self) -> None:
        """ Close the directive. """

    @contextlib.contextmanager
    def directive(self,
                  name: str,
                  value: Optional[str] = None,
                  options: Optional[list[str]] = None):
        """ Open the directive context. """
        self.open_directive(name, value, options)
        yield
        self.close_directive()

    def open_latex_environment(self, environment: str) -> None:
        """ Open a LaTeX environment. """
        line_context = self.push_line_context()
        with self.directive("raw", "latex"):
            self.add(f"\\begin{{{environment}}}")
        line_context.content_begin(self)

    def close_latex_environment(self, environment: str) -> None:
        """ Close a LaTeX environment. """
        line_context = self.pop_line_context()
        with self.directive("raw", "latex"):
            self.add(f"\\end{{{environment}}}")
        self.check_line_context(line_context)

    @contextlib.contextmanager
    def latex_environment(self,
                          environment: str,
                          use: bool = True) -> Iterator[None]:
        """ Open a LaTeX environment context. """
        if use:
            self.open_latex_environment(environment)
            yield
            self.close_latex_environment(environment)
        else:
            yield

    def open_latex_font_size(self, size: str | int = "tiny") -> None:
        """ Open a LaTeX font size environment. """
        self.open_latex_environment(_latex_font_size(size))

    def close_latex_font_size(self, size: str | int = "tiny") -> None:
        """ Close a LaTeX font size environment. """
        self.close_latex_environment(_latex_font_size(size))

    @contextlib.contextmanager
    def latex_font_size(self,
                        size: str | int = "tiny",
                        use: bool = True) -> Iterator[None]:
        """ Open a LaTeX font size environment context. """
        with self.latex_environment(_latex_font_size(size), use):
            yield

    @abc.abstractmethod
    def add_definition_item(self, name: GenericContent,
                            definition: GenericContent) -> None:
        """ Add the definition item the content. """

    @abc.abstractmethod
    def add_glossary_term(self, term: str, definition: str) -> None:
        """ Add the glossary term the content. """

    def add_code_block(self,
                       code: list[str],
                       language: str = "none",
                       font_size: str | int = "footnotesize",
                       line_number_start: int = 1) -> None:
        """ Add the code block. """


class TextMapper(ItemMapper):
    """ Provides an item mapper for text. """

    def __init__(self, item: Item):
        super().__init__(item)
        self.add_get_value("glossary/term:/term", self._get_glossary_term)
        self.add_get_value("glossary/term:/plural", self._get_glossary_plural)

    @abc.abstractmethod
    def create_content(
            self,
            section_level: int = 0,
            the_license: str | set[str] | None = None) -> TextContent:
        """ Create a content object for text production. """

    def _get_glossary_term(self, ctx: ItemGetValueContext) -> str:
        return self.create_content().term(ctx.value[ctx.key],
                                          ctx.item.view.get("term", None))

    def _get_glossary_plural(self, ctx: ItemGetValueContext) -> str:
        return self.create_content().term(get_value_plural(ctx),
                                          ctx.item.view.get("term", None))
