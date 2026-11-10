# SPDX-License-Identifier: BSD-2-Clause
""" Provides the parser and the resolver of attribute paths. """

# Copyright (C) 2026 embedded brains GmbH & Co. KG
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

from collections.abc import Iterator, MutableMapping
import dataclasses
import functools
import re
from typing import Any, Callable, Optional

_SEGMENT = re.compile(r"([^/\[\]]+)(?:\[(-?[0-9]+)\])?")

_SELECTOR = re.compile(r"([^/\[\]]+)(?:\[(.*)\])?", re.DOTALL)

_INDEX = re.compile(r"-?[0-9]+")

_NAME = re.compile(r"[^\s()=\"'\[\]/]+")

_SPACE = re.compile(r"\s*")

_QUOTES = "\"'"

_SCALAR_TYPES = ("str", "int", "float", "bool")

_TYPES = (*_SCALAR_TYPES, "null", "list", "dict")

_ANY_KEY = "*"

_ANY_DEPTH = "**"

_WILDCARDS = (_ANY_KEY, _ANY_DEPTH)


@dataclasses.dataclass(frozen=True)
class AttributePathSegment:
    """
    Is one segment of an attribute path.

    The key selects a value of a mapping.  The index selects an element of the
    list which the key selects.  A negative index counts from the end of the
    list.  None means that the segment has no index.
    """
    key: str
    index: Optional[int] = None

    def __str__(self) -> str:
        if self.index is None:
            return self.key
        return f"{self.key}[{self.index}]"


@functools.lru_cache(maxsize=4096)
def parse_attribute_segment(segment: str) -> AttributePathSegment:
    """
    Parse the attribute path segment.

    Args:
        segment: The segment in the form ``key`` or ``key[index]``.

    Returns:
        The parsed segment.

    Raises:
        ValueError: The segment has an empty key, a wildcard key or an invalid
            index.
    """
    match = _SEGMENT.fullmatch(segment)
    if match is None or match.group(1) in _WILDCARDS:
        raise ValueError(f"invalid attribute path segment '{segment}'")
    index = match.group(2)
    return AttributePathSegment(match.group(1),
                                None if index is None else int(index))


@functools.lru_cache(maxsize=4096)
def parse_attribute_path(path: str) -> tuple[AttributePathSegment, ...]:
    """
    Parse the attribute path.

    Args:
        path: The segments separated by slashes.  A leading and a trailing
            slash are ignored.

    Returns:
        The parsed segments.  The empty tuple denotes the root.

    Raises:
        ValueError: A segment is invalid.
    """
    stripped = path.strip("/")
    if not stripped:
        return ()
    segments = []
    for segment in stripped.split("/"):
        try:
            segments.append(parse_attribute_segment(segment))
        except ValueError as err:
            raise ValueError(f"invalid segment '{segment}' in attribute "
                             f"path '{path}'") from err
    return tuple(segments)


def _error(err: Exception, path: str,
           segment: AttributePathSegment) -> Exception:
    return type(err)(f"cannot resolve segment '{segment}' of attribute path "
                     f"'{path}': {err}")


def get_segment_value(data: Any, path: str,
                      segment: AttributePathSegment) -> Any:
    """
    Get the value which the segment of the attribute path selects.

    Args:
        data: The value which contains the segment.
        path: The attribute path, used by the error messages.
        segment: The segment.

    Returns:
        The selected value.

    Raises:
        KeyError: The key or the index does not exist.
        IndexError: The index is out of range.
        TypeError: A value cannot take the key or the index.
    """
    try:
        value = data[segment.key]
        if segment.index is not None:
            value = value[segment.index]
    except (KeyError, IndexError, TypeError) as err:
        raise _error(err, path, segment) from err
    return value


def resolve_attribute_path(data: Any,
                           path: str) -> tuple[Any, str, Optional[int]]:
    """
    Resolve the attribute path to the container of its last segment.

    Args:
        data: The value at the root of the path.
        path: The attribute path.

    Returns:
        The container, the key and the index of the last segment.  The key
        selects a value of the container.  The index, if not None, selects an
        element of that value.

    Raises:
        ValueError: The path is invalid or denotes the root.
        KeyError: The key or the index of a segment does not exist.
        IndexError: The index of a segment is out of range.
        TypeError: A value cannot take the key or the index of a segment, or
            the container is no mutable mapping.
    """
    segments = parse_attribute_path(path)
    if not segments:
        raise ValueError(f"the attribute path '{path}' denotes the root")
    container = data
    for segment in segments[:-1]:
        container = get_segment_value(container, path, segment)
    last = segments[-1]
    if not isinstance(container, MutableMapping):
        raise _error(TypeError("the value is no mutable mapping"), path, last)
    return container, last.key, last.index


@dataclasses.dataclass(frozen=True)
class AttributePathMatch:
    """
    Is a node which an attribute path selects.

    The key selects a value of the container.  The index, if not None, selects
    an element of that value.
    """
    container: MutableMapping
    key: str
    index: Optional[int] = None

    @property
    def value(self) -> Any:
        """ Is the selected value. """
        value = self.container[self.key]
        if self.index is not None:
            value = value[self.index]
        return value


_Predicate = Callable[[Any], bool]

_TYPE_NAMES = ((bool, "bool"), (int, "int"), (float, "float"), (str, "str"),
               (type(None), "null"), (list, "list"), (MutableMapping, "dict"))


def _type_name(value: Any) -> str:
    for the_type, name in _TYPE_NAMES:
        if isinstance(value, the_type):
            return name
    return ""


def _scalar_text(value: Any) -> Optional[str]:
    type_name = _type_name(value)
    if type_name == "bool":
        return "true" if value else "false"
    if type_name in _SCALAR_TYPES:
        return str(value)
    return None


def _text_matches(pattern: Optional[re.Pattern], value: Any) -> bool:
    if pattern is None:
        return True
    text = _scalar_text(value)
    return text is not None and pattern.fullmatch(text) is not None


class _ExpressionParser:
    # pylint: disable=too-few-public-methods

    def __init__(self, segment: str, text: str) -> None:
        self._segment = segment
        self._text = text
        self._position = 0

    def parse(self) -> _Predicate:
        """ Parse the selection expression. """
        predicate = self._or()
        self._skip_space()
        if self._position != len(self._text):
            raise self._error("unexpected text")
        return predicate

    def _error(self, message: str) -> ValueError:
        return ValueError(f"invalid attribute path segment '{self._segment}':"
                          f" {message} at position {self._position} of the "
                          f"selection '{self._text}'")

    def _skip_space(self) -> None:
        match = _SPACE.match(self._text, self._position)
        assert match is not None
        self._position = match.end()

    def _take(self, token: str) -> bool:
        self._skip_space()
        if self._text.startswith(token, self._position):
            self._position += len(token)
            return True
        return False

    def _keyword(self, word: str) -> bool:
        self._skip_space()
        end = self._position + len(word)
        if self._text.startswith(word, self._position) and (end == len(
                self._text) or not self._text[end].isalnum()):
            self._position = end
            return True
        return False

    def _expect(self, token: str) -> None:
        if not self._take(token):
            raise self._error(f"expected '{token}'")

    def _or(self) -> _Predicate:
        operands = [self._and()]
        while self._keyword("or"):
            operands.append(self._and())
        if len(operands) == 1:
            return operands[0]
        return lambda value: any(operand(value) for operand in operands)

    def _and(self) -> _Predicate:
        operands = [self._not()]
        while self._keyword("and"):
            operands.append(self._not())
        if len(operands) == 1:
            return operands[0]
        return lambda value: all(operand(value) for operand in operands)

    def _not(self) -> _Predicate:
        if self._keyword("not"):
            operand = self._not()
            return lambda value: not operand(value)
        return self._primary()

    def _primary(self) -> _Predicate:
        if self._take("("):
            predicate = self._or()
            self._expect(")")
            return predicate
        if self._take("attr("):
            return self._attr()
        if self._take("type("):
            return self._type()
        raise self._error("expected a predicate")

    def _name(self) -> str:
        self._skip_space()
        match = _NAME.match(self._text, self._position)
        if match is None:
            raise self._error("expected a name")
        self._position = match.end()
        return match.group(0)

    def _string(self) -> str:
        self._skip_space()
        if self._position == len(
                self._text) or self._text[self._position] not in _QUOTES:
            raise self._error("expected a quoted string")
        quote = self._text[self._position]
        chars: list[str] = []
        position = self._position + 1
        while position < len(self._text):
            char = self._text[position]
            if char == quote:
                self._position = position + 1
                return "".join(chars)
            if char == "\\" and self._text[position + 1:position +
                                           2] in (quote, "\\"):
                position += 1
                char = self._text[position]
            chars.append(char)
            position += 1
        raise self._error("unterminated string")

    def _pattern(self) -> Optional[re.Pattern]:
        if not self._take("="):
            return None
        string = self._string()
        try:
            return re.compile(string)
        except re.error as err:
            raise ValueError(
                f"invalid regular expression in attribute path segment "
                f"'{self._segment}': {err}") from err

    def _attr(self) -> _Predicate:
        name = self._name()
        self._expect(")")
        pattern = self._pattern()

        def _predicate(value: Any) -> bool:
            return isinstance(
                value, MutableMapping) and name in value and (_text_matches(
                    pattern, value[name]))

        return _predicate

    def _type(self) -> _Predicate:
        type_name = self._name()
        if type_name not in _TYPES:
            raise self._error(f"unknown type '{type_name}'")
        self._expect(")")
        pattern = self._pattern()
        if pattern is not None and type_name not in _SCALAR_TYPES:
            raise self._error(f"the type '{type_name}' takes no regular "
                              "expression")
        return lambda value: _type_name(value) == type_name and _text_matches(
            pattern, value)


@dataclasses.dataclass(frozen=True)
class _Selector:
    key: str
    index: Optional[int] = None
    all_elements: bool = False
    predicate: Optional[_Predicate] = None

    def select(self, data: Any) -> Iterator[AttributePathMatch]:
        """ Yield the nodes of the data which the selector selects. """
        if not isinstance(data, MutableMapping):
            return
        keys = list(data) if self.key == _ANY_KEY else [self.key]
        for key in keys:
            if key in data:
                yield from self._select_value(data, key)

    def _select_value(self, data: MutableMapping,
                      key: str) -> Iterator[AttributePathMatch]:
        value = data[key]
        if self.index is not None:
            if isinstance(value,
                          list) and -len(value) <= self.index < len(value):
                yield AttributePathMatch(data, key, self.index % len(value))
        elif self.all_elements or self.predicate is not None:
            if isinstance(value, list):
                for index, element in enumerate(value):
                    if self.predicate is None or self.predicate(element):
                        yield AttributePathMatch(data, key, index)
        else:
            yield AttributePathMatch(data, key)


def _split_selection_path(path: str) -> list[str]:
    segments: list[str] = []
    start = 0
    depth = 0
    quote = ""
    escape = False
    for position, char in enumerate(path):
        if escape:
            escape = False
        elif quote:
            if char == "\\":
                escape = True
            elif char == quote:
                quote = ""
        elif char in _QUOTES and depth > 0:
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]" and depth > 0:
            depth -= 1
        elif char == "/" and depth == 0:
            segments.append(path[start:position])
            start = position + 1
    segments.append(path[start:])
    return segments


def _parse_selector(segment: str) -> _Selector:
    if segment == _ANY_DEPTH:
        return _Selector(_ANY_DEPTH)
    match = _SELECTOR.fullmatch(segment)
    if match is None or match.group(1) == _ANY_DEPTH:
        raise ValueError(f"invalid attribute path segment '{segment}'")
    key, selection = match.groups()
    if selection is None:
        return _Selector(key)
    if _INDEX.fullmatch(selection):
        return _Selector(key, index=int(selection))
    if selection == "*":
        return _Selector(key, all_elements=True)
    return _Selector(key,
                     predicate=_ExpressionParser(segment, selection).parse())


@functools.lru_cache(maxsize=4096)
def _parse_selection_path(path: str) -> tuple[_Selector, ...]:
    stripped = path.strip("/")
    if not stripped:
        raise ValueError(f"the attribute path '{path}' denotes the root")
    return tuple(
        _parse_selector(segment)
        for segment in _split_selection_path(stripped))


def _children(data: Any) -> Iterator[AttributePathMatch]:
    if isinstance(data, MutableMapping):
        for key, value in data.items():
            yield AttributePathMatch(data, key)
            if isinstance(value, list):
                for index in range(len(value)):
                    yield AttributePathMatch(data, key, index)


def _select(data: Any, selectors: tuple[_Selector, ...],
            matches: list[AttributePathMatch]) -> None:
    selector = selectors[0]
    rest = selectors[1:]
    if selector.key == _ANY_DEPTH:
        if rest:
            _select(data, rest, matches)
        for child in _children(data):
            if not rest:
                matches.append(child)
            _select(child.value, selectors, matches)
        return
    for match in selector.select(data):
        if rest:
            _select(match.value, rest, matches)
        else:
            matches.append(match)


def select_attribute_path(data: Any, path: str) -> list[AttributePathMatch]:
    """
    Select the nodes of the data which the attribute path selects.

    In addition to the forms of a plain attribute path, a segment may take
    these selection forms:

    * ``*`` selects every key of a mapping.

    * ``**`` stands for any number of segments, zero included.  As the last
      segment, it selects every node below.

    * ``key[*]`` selects every element of the list.

    * ``key[<expression>]`` selects each element of the list for which the
      boolean expression is true.

    An expression combines predicates with ``and``, ``or``, ``not`` and
    parentheses.  The operators bind as in Python.  These are the
    predicates:

    * ``attr(<name>)`` is true for a mapping with the key.

    * ``attr(<name>)="<regex>"`` is true for a mapping whose value of the key
      is a scalar with a matching text.

    * ``type(<type>)`` is true for a value of the type.  The types are
      ``str``, ``int``, ``float``, ``bool``, ``null``, ``list`` and ``dict``.

    * ``type(<type>)="<regex>"`` is true for a scalar value of the type with a
      matching text.  The type is ``str``, ``int``, ``float`` or ``bool``.

    A regular expression matches the whole YAML text of the scalar, such as
    ``true`` for a boolean.  It is a string in double or single quotes.  A
    backslash escapes the quote and the backslash.  Inside the quotes, each
    character belongs to the string.  A slash inside the brackets does not
    end the segment.  A missing key, an index out of range and a value of
    another type select nothing.

    Args:
        data: The value at the root of the path.
        path: The attribute path.

    Returns:
        The selected nodes in the order of the data.

    Raises:
        ValueError: The path is invalid or denotes the root.
    """
    matches: list[AttributePathMatch] = []
    _select(data, _parse_selection_path(path), matches)
    return matches
