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

from collections.abc import MutableMapping
import dataclasses
import functools
import re
from typing import Any, Optional

_SEGMENT = re.compile(r"([^/\[\]]+)(?:\[(-?[0-9]+)\])?")


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
        ValueError: The segment has an empty key or an invalid index.
    """
    match = _SEGMENT.fullmatch(segment)
    if match is None:
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
