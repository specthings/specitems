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

from specitems import EmptyItemCache, Item, ItemMapper
from specitems.attributepath import (AttributePathMatch, AttributePathSegment,
                                     get_segment_value, parse_attribute_path,
                                     parse_attribute_segment,
                                     resolve_attribute_path,
                                     select_attribute_path)


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


@pytest.mark.parametrize("segment", [
    "", "[0]", "a[", "a]", "a[]", "a[x]", "a[0]b", "a[0][1]", "a/b", "a[ 1]",
    "*", "**", "*[0]", "a[*]", "a[~b]", "a[b~c]"
])
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


_SELECT = {
    "a":
    "b",
    "links": [{
        "role": "x",
        "uid": "/rtems/foo"
    }, {
        "role": "y",
        "uid": "/rtems/bar"
    }, "z"],
    "enabled-by": ["s/a", 1, "s/b", "t"],
    "m": {
        "a": "c",
        "n": {
            "a": "d"
        }
    },
}


def _matches(path):
    return [(id(match.container), match.key, match.index)
            for match in select_attribute_path(_SELECT, path)]


def _match(container, key, index=None):
    return (id(container), key, index)


def test_select_attribute_path_plain():
    assert _matches("/a") == [_match(_SELECT, "a")]
    assert _matches("/m/n/a") == [_match(_SELECT["m"]["n"], "a")]
    assert _matches("/links[1]/uid") == [_match(_SELECT["links"][1], "uid")]
    assert _matches("/links[-3]") == [_match(_SELECT, "links", 0)]
    assert _matches("/links[3]") == []
    assert _matches("/a[0]") == []
    assert _matches("/x") == []
    assert _matches("/a/b") == []


def test_select_attribute_path_any_key():
    assert _matches("/*") == [
        _match(_SELECT, "a"),
        _match(_SELECT, "links"),
        _match(_SELECT, "enabled-by"),
        _match(_SELECT, "m")
    ]
    assert _matches("/*/a") == [_match(_SELECT["m"], "a")]
    assert _matches("/*[0]") == [
        _match(_SELECT, "links", 0),
        _match(_SELECT, "enabled-by", 0)
    ]


def test_select_attribute_path_any_depth():
    assert _matches("/**/a") == [
        _match(_SELECT, "a"),
        _match(_SELECT["m"], "a"),
        _match(_SELECT["m"]["n"], "a")
    ]
    assert _matches("/m/**") == [
        _match(_SELECT["m"], "a"),
        _match(_SELECT["m"], "n"),
        _match(_SELECT["m"]["n"], "a")
    ]
    assert _matches("/**/uid") == [
        _match(_SELECT["links"][0], "uid"),
        _match(_SELECT["links"][1], "uid")
    ]
    assert len(_matches("/**")) == 18
    assert select_attribute_path("x", "/**") == []


def test_select_attribute_path_elements():
    assert _matches("/links[*]") == [
        _match(_SELECT, "links", 0),
        _match(_SELECT, "links", 1),
        _match(_SELECT, "links", 2)
    ]
    assert _matches("/links[*]/role") == [
        _match(_SELECT["links"][0], "role"),
        _match(_SELECT["links"][1], "role")
    ]
    assert _matches("/a[*]") == []


def test_select_attribute_path_conditions():
    assert _matches('/links[attr(uid)="/rtems/f.*"]') == [
        _match(_SELECT, "links", 0)
    ]
    assert _matches("/links[attr(uid)='/rtems/.*']/role") == [
        _match(_SELECT["links"][0], "role"),
        _match(_SELECT["links"][1], "role")
    ]
    assert _matches('/links[attr(uid)="/rtems"]') == []
    assert _matches('/links[attr(role)="[xy]"]') == [
        _match(_SELECT, "links", 0),
        _match(_SELECT, "links", 1)
    ]
    assert _matches(r'/links[attr(role)="\]"]') == []
    assert _matches('/links[attr(nope)=".*"]') == []
    assert _matches("/links[attr(role)]") == [
        _match(_SELECT, "links", 0),
        _match(_SELECT, "links", 1)
    ]
    assert _matches('/enabled-by[type(str)="s/.*"]') == [
        _match(_SELECT, "enabled-by", 0),
        _match(_SELECT, "enabled-by", 2)
    ]
    assert _matches('/enabled-by[type(int)="1"]') == [
        _match(_SELECT, "enabled-by", 1)
    ]
    assert _matches("/links[type(str)]") == [_match(_SELECT, "links", 2)]
    assert _matches("/links[type(dict)]") == [
        _match(_SELECT, "links", 0),
        _match(_SELECT, "links", 1)
    ]


_TYPED = {
    "list":
    [True, 1, 1.5, "x", None, [], {}, {
        "a": True
    }, {
        "a": None
    }, {
        "a": [1]
    }]
}


def _typed(selection):
    return [
        match.index
        for match in select_attribute_path(_TYPED, f"/list[{selection}]")
    ]


@pytest.mark.parametrize("selection, indices", [
    ("type(bool)", [0]),
    ('type(bool)="true"', [0]),
    ('type(bool)="True"', []),
    ("type(int)", [1]),
    ('type(float)="1.5"', [2]),
    ('type(str)="x"', [3]),
    ("type(null)", [4]),
    ("type(list)", [5]),
    ("type(dict)", [6, 7, 8, 9]),
    ('attr(a)="true"', [7]),
    ('attr(a)=".*"', [7]),
    ("attr(a)", [7, 8, 9]),
    ("type(int) or type(str)", [1, 3]),
    ("type(dict) and not attr(a)", [6]),
    ("not type(dict) and not type(list)", [0, 1, 2, 3, 4]),
    ('type(dict) and (attr(a)="true" or not attr(a))', [6, 7]),
    ("not not type(null)", [4]),
    ('  type( str )  =  "x"  ', [3]),
    (r'type(int)="\d"', [1]),
    (r"type(str)='\''", []),
    (r'type(str)="\\\\"', []),
])
def test_select_attribute_path_expressions(selection, indices):
    assert _typed(selection) == indices


def test_select_attribute_path_quoted_slash():
    data = {"a": [{"b": "x/y]"}], "x/y]": 1}
    assert select_attribute_path(data, '/a[attr(b)="x/y]"]/b') == [
        AttributePathMatch(data["a"][0], "b")
    ]
    assert select_attribute_path(data, "/a[attr(b)='x/y\\']']") == []


def test_select_attribute_path_match_value():
    match = select_attribute_path(_SELECT, '/links[attr(uid)="/rtems/bar"]')[0]
    assert match == AttributePathMatch(_SELECT, "links", 1)
    assert match.value == _SELECT["links"][1]
    assert select_attribute_path(_SELECT, "/m/a")[0].value == "c"


@pytest.mark.parametrize("path,message", [
    ("/", r"'/' denotes the root"),
    ("/a//b", r"invalid attribute path segment ''"),
    ("/a[x]", r"invalid attribute path segment 'a\[x\]'"),
    ("/**[0]", r"invalid attribute path segment '\*\*\[0\]'"),
    ('/a[attr(b)="("]', r"invalid regular expression in attribute path "
     r"segment"),
    ("/a[b]", r"expected a predicate at position 0 of the selection 'b'"),
    ("/a[attr(b) x]", r"unexpected text at position 8"),
    ("/a[(attr(b)]", r"expected '\)'"),
    ("/a[attr()]", r"expected a name"),
    ("/a[attr(b]", r"expected '\)'"),
    ("/a[attr(b)=x]", r"expected a quoted string"),
    ("/a[attr(b)=]", r"expected a quoted string"),
    ("/a[attr(b)='x]", r"unterminated string"),
    ("/a[type(x)]", r"unknown type 'x'"),
    ("/a[type(dict)='x']", r"the type 'dict' takes no regular expression"),
    ("/a[not]", r"expected a predicate"),
])
def test_select_attribute_path_invalid(path, message):
    with pytest.raises(ValueError, match=message):
        select_attribute_path(_SELECT, path)


@pytest.mark.parametrize(
    "path",
    ["/*", "/links[*]", '/links[attr(uid)=".*"]', '/enabled-by[type(str)]'])
def test_map_selection_path(path):
    item = Item(EmptyItemCache(), "/x", _SELECT)
    mapper = ItemMapper(item)
    with pytest.raises(ValueError, match=r"cannot get value for"):
        mapper.map(f".:{path}")
    with pytest.raises(ValueError, match=r"malformed substitution variable"):
        mapper.substitute(f"${{.:{path}}}")


def test_select_attribute_path_other_type():
    assert select_attribute_path({"a": [(1, )]}, "/a[type(list)]") == []
