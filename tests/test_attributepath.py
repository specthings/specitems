# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the attributepath module. """

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

import pytest

from specitems.attributepath import (AttributePathSegment, get_segment_value,
                                     parse_attribute_path,
                                     parse_attribute_segment,
                                     resolve_attribute_path)


def test_segment_str():
    assert str(AttributePathSegment("a")) == "a"
    assert str(AttributePathSegment("a", 0)) == "a[0]"
    assert str(AttributePathSegment("a", -1)) == "a[-1]"


@pytest.mark.parametrize("segment,key,index", [
    ("a", "a", None),
    ("a-b.c", "a-b.c", None),
    ("a[0]", "a", 0),
    ("list-2[12]", "list-2", 12),
    ("a[-1]", "a", -1),
])
def test_parse_attribute_segment(segment, key, index):
    assert parse_attribute_segment(segment) == AttributePathSegment(key, index)


@pytest.mark.parametrize(
    "segment",
    ["", "[0]", "a[", "a]", "a[]", "a[x]", "a[0]b", "a[0][1]", "a/b", "a[ 1]"])
def test_parse_attribute_segment_invalid(segment):
    with pytest.raises(ValueError, match=r"invalid attribute path segment"):
        parse_attribute_segment(segment)


def test_parse_attribute_path():
    assert parse_attribute_path("") == ()
    assert parse_attribute_path("/") == ()
    assert parse_attribute_path("//") == ()
    assert parse_attribute_path("a") == (AttributePathSegment("a"), )
    assert parse_attribute_path("/a/") == (AttributePathSegment("a"), )
    assert parse_attribute_path("/list-2[0]/a") == (AttributePathSegment(
        "list-2", 0), AttributePathSegment("a"))
    assert parse_attribute_path("/a[-2]") == (AttributePathSegment("a", -2), )


@pytest.mark.parametrize("path,segment", [("/a//b", ""), ("/a/b[x]", "b[x]")])
def test_parse_attribute_path_invalid(path, segment):
    with pytest.raises(ValueError) as err:
        parse_attribute_path(path)
    assert str(err.value) == (f"invalid segment '{segment}' in attribute "
                              f"path '{path}'")


_DATA = {"a": "b", "c": ["d", "e", {"f": {"g": "h"}}]}


def test_get_segment_value():
    assert get_segment_value(_DATA, "/a", AttributePathSegment("a")) == "b"
    assert get_segment_value(_DATA, "/c[1]", AttributePathSegment("c",
                                                                  1)) == "e"
    assert get_segment_value(_DATA, "/c[-1]",
                             AttributePathSegment("c", -1)) == {
                                 "f": {
                                     "g": "h"
                                 }
                             }


@pytest.mark.parametrize("segment,error", [
    (AttributePathSegment("x"), KeyError),
    (AttributePathSegment("c", 3), IndexError),
    (AttributePathSegment("a", 1), IndexError),
])
def test_get_segment_value_error(segment, error):
    with pytest.raises(error) as err:
        get_segment_value(_DATA, "/p", segment)
    assert f"cannot resolve segment '{segment}' of attribute path '/p'" in str(
        err.value)


def test_get_segment_value_type_error():
    with pytest.raises(TypeError, match=r"segment 'x' of attribute path '/p'"):
        get_segment_value("abc", "/p", AttributePathSegment("x"))


def test_resolve_attribute_path():
    assert resolve_attribute_path(_DATA, "/a") == (_DATA, "a", None)
    assert resolve_attribute_path(_DATA, "/c[2]/f/g") == (_DATA["c"][2]["f"],
                                                          "g", None)
    assert resolve_attribute_path(_DATA, "/c[-1]") == (_DATA, "c", -1)
    assert resolve_attribute_path(_DATA, "/new") == (_DATA, "new", None)


def test_resolve_attribute_path_error():
    with pytest.raises(ValueError, match=r"'/' denotes the root"):
        resolve_attribute_path(_DATA, "/")
    with pytest.raises(ValueError, match=r"invalid segment"):
        resolve_attribute_path(_DATA, "/a//b")
    with pytest.raises(KeyError, match=r"segment 'x' of attribute path"):
        resolve_attribute_path(_DATA, "/x/y")
    with pytest.raises(IndexError,
                       match=r"segment 'c\[9\]' of attribute path"):
        resolve_attribute_path(_DATA, "/c[9]/y")
    with pytest.raises(TypeError,
                       match=r"segment 'y' of attribute path "
                       r"'/a/y': the value is no mutable mapping"):
        resolve_attribute_path(_DATA, "/a/y")
    with pytest.raises(TypeError, match=r"the value is no mutable mapping"):
        resolve_attribute_path(1, "/y")
    with pytest.raises(TypeError,
                       match=r"segment 'x' of attribute path "
                       r"'/c/x': the value is no mutable mapping"):
        resolve_attribute_path(_DATA, "/c/x")
