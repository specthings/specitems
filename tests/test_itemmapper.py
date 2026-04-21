# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the itemmapper module. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
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

from specitems import (EmptyItem, ItemCache, ItemGetValueContext, ItemMapper,
                       ItemValueProvider, SpecTypeProvider, get_value_default,
                       unpack_arg, unpack_args)

from .util import create_item_cache_config, get_other_type_data_by_uid


def _get_x_to_b_value(ctx):
    assert ctx.key == "x-to-b"
    args = ctx.args if ctx.args is not None else ""
    return ctx.value["b"] + args


def _get_value_default(ctx):
    return "default"


def _get_value_dict(ctx):
    return ctx.key


def _get_value_other_item(ctx):
    uid_end = ctx.remaining_path.find("/")
    other = ctx.item.cache[f"/{ctx.remaining_path[:uid_end]}"]
    return ctx.reset(other, ctx.remaining_path[uid_end + 1:])


def test_item_mapper(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache")
    config.enabled_set = ["foobar"]
    type_provider = SpecTypeProvider(get_other_type_data_by_uid())
    item_cache = ItemCache(config, type_provider=type_provider)
    assert "/spec/root" in item_cache
    p = item_cache["/p"]
    assert p.type == "other"
    base_mapper = ItemMapper(p)
    assert base_mapper["d/c:v"] == "c"
    mapper = ItemMapper(p)
    assert mapper.substitute(None) == ""
    assert mapper.substitute(None, prefix="v") == ""
    assert mapper.map(".:../x/y", prefix="v")[2] == "z"
    item_2, key_path_2, value_2 = mapper.map(".:.", prefix="v")
    assert item_2 == p
    assert key_path_2 == "/v"
    assert value_2 == "p"
    c = item_cache["/c"]
    assert mapper.substitute("${.:/v}", item=c) == "c"
    assert mapper.substitute("${*:/v}", item=c) == "p"
    assert mapper.substitute("${.:v}", item=c, prefix="/u") == "C"
    assert mapper.substitute("${*:v}", item=c, prefix="/u") == "p"
    assert mapper.substitute_data(["${.:/v}"], item=c) == ["c"]
    assert mapper.substitute_data(["${*:/v}"], item=c) == ["p"]
    assert mapper.substitute("$$${.:.}", prefix="v") == "$p"
    assert mapper.substitute_data(None) == None
    assert mapper.substitute_data("x") == "x"
    assert mapper.substitute_data(["x"]) == ["x"]
    assert mapper.substitute_data(["1", "${/c:/v}", "${/c:/w}",
                                   42]) == ["1", "c", "u", "v", 42]
    assert mapper.substitute_data(["1", " ${/c:/r} ", 2]) == ["1", " c ", 2]
    assert mapper.substitute_data(["1", "${/c:/r}", 2]) == ["1", "c", 2]
    assert mapper.substitute_data(["1", " $${/c:/r} ",
                                   2]) == ["1", " ${/c:/r} ", 2]
    assert mapper.substitute_data(["1", "$${/c:/r}",
                                   2]) == ["1", "${/c:/r}", 2]
    assert mapper.substitute_data({"x": "y"}) == {"x": "y"}
    assert mapper.substitute_data({"${/c:/v}": "y"}) == {"c": "y"}
    assert mapper.item == p
    with mapper.scope(item_cache["/c"]):
        assert mapper.item == item_cache["/c"]
    assert mapper.item == p
    assert mapper.map(".:.", prefix="x/y")[2] == "z"
    match = r"cannot get value for '/v' of spec:/proxy specified by 'proxy:/v"
    with pytest.raises(ValueError, match=match):
        mapper["proxy:/v"]
    proxy = item_cache["/proxy"]
    assert proxy.is_proxy()
    assert proxy.type == "proxy"
    s = item_cache["/proxy2"]
    assert not s.is_proxy()
    assert s is item_cache["/s"]
    assert s.uid == "/s"
    assert s.ident == "S"
    assert [(link.item.uid, link.role)
            for link in s.links_to_parents()] == [("/s", "proxy-member"),
                                                  ("/r", "xyz")]
    assert [(link.item.uid, link.role)
            for link in s.links_to_children()] == [("/c", "oops")]
    assert mapper["proxy2:/v"] == "s"
    assert item_cache["/r"].child("xyz").uid == "/s"
    assert mapper["d/c:v"] == "c"
    assert mapper["d/c:a/b"] == "e"
    mapper.add_get_value("other:/a/x-to-b", _get_x_to_b_value)
    assert mapper["d/c:a/x-to-b:args:0:%"] == "eargs:0:%"
    assert mapper["d/c:a/f[1]"] == 2
    assert mapper["d/c:a/../a/f[3]/g[0]"] == 4
    item_3, key_path_3, value_3 = mapper.map("/p:/v")
    assert item_3 == p
    assert key_path_3 == "/v"
    assert value_3 == "p"
    mapper.add_default_get_value("default", _get_value_default)
    assert mapper["p:/default"] == "default"
    mapper.add_get_value_dictionary("other:/dict", _get_value_dict)
    assert mapper["d/c:/dict/some-arbitrary-key"] == "some-arbitrary-key"
    assert mapper["d/c:/default"] == "default"
    mapper.add_get_value("other:/other", _get_value_other_item)
    assert mapper["d/c:/other/s/v"] == "s"
    assert mapper.substitute("${.:/r1/r2/r3}") == "foobar"
    assert mapper[".:/r1/r2/r3"] == "foobar"
    match = r"substitution for spec:/p using prefix 'blub' failed for text:\n    1: \${}"
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${}", p, "blub")
    match = r"item 'boom' relative to spec:/p specified by 'boom:bam' does not exist"
    with pytest.raises(ValueError, match=match):
        mapper.map("boom:bam", p, "blub")
    match = r"cannot get value for 'blub/bam' of spec:/p specified by '.:bam'"
    with pytest.raises(ValueError, match=match):
        mapper.map(".:bam", p, "blub")

    # Remove proxy member
    item_cache.remove_item("/s")


def test_empty_item_mapper():
    item = EmptyItem()
    mapper = ItemMapper(item)
    assert mapper.item == item
    item_2 = EmptyItem()
    mapper.item = item_2
    assert mapper.item == item_2


def _transformer_x(value, a, b, c="c"):
    return f"{value}/{a}/{b}/{c}"


def _transformer_y(value):
    return f"<{value}>"


def test_item_mapper_transformer():
    item = EmptyItem()
    item["SPDX-License-Identifier"] = "BSD-2-Clause"
    item["copyrights"] = []
    item["k"] = "v"
    mapper = ItemMapper(item)
    mapper.add_value_transformer("x", _transformer_x)
    mapper.add_value_transformer("y", _transformer_y)
    assert mapper.substitute("${.:/k:x c=C,A,B}") == "v/A/B/C"
    assert mapper.substitute("${.:/k:x A,B}") == "v/A/B/c"
    with pytest.raises(ValueError):
        mapper.substitute("${.:/k:x A}")
    assert mapper.substitute("${.:/k:y}") == "<v>"


class _ValueProvider(ItemValueProvider):

    def __init__(self, mapper: ItemMapper) -> None:
        super().__init__(mapper)
        self.counter = 0

    def reset(self) -> None:
        self.counter += 1


def test_item_value_provider():
    mapper = ItemMapper(EmptyItem())
    provider = _ValueProvider(mapper)
    assert provider.counter == 0
    mapper.reset()
    assert provider.counter == 1


def test_item_get_value_context():
    item = EmptyItem()
    item["SPDX-License-Identifier"] = "BSD-2-Clause"
    item["copyrights"] = []
    item["ik"] = "iv"
    mapper = ItemMapper(item)
    mapper.add_value_transformer("x", _transformer_x)

    remaining_path = "abc"
    args = "A,a=b,B,c=d,e==%,C"
    value = {"k": "v"}
    ctx = ItemGetValueContext(item, remaining_path, args, value, mapper, {})
    assert ctx.item == item
    assert ctx.remaining_path == remaining_path
    assert ctx.args == args
    assert ctx.value == value
    assert ctx.mapper == mapper
    assert ctx.get_value_map == {}
    assert ctx.path == ""
    assert ctx.key_index == ""
    assert ctx.key == ""
    assert ctx.index == -1
    assert ctx.arg("a") == "b"
    assert ctx.arg("x", "y") == "y"
    assert ctx.unpack_args_list() == ["A", "a=b", "B", "c=d", "e==$", "C"]
    assert ctx.unpack_args_dict() == (["A", "B", "C"], {
        "a": "b",
        "c": "d",
        "e": "=$"
    })

    args_none = None
    ctx_2 = ItemGetValueContext(item, remaining_path, args_none, value, mapper,
                                {})
    assert ctx_2.unpack_args_list() == []
    assert ctx_2.unpack_args_dict() == ([], {})

    ctx_3 = ItemGetValueContext(item,
                                remaining_path,
                                args_none,
                                value,
                                mapper, {},
                                key="k")
    assert ctx_3.key == "k"
    assert ctx_3.substitute_and_transform("${.:/ik}") == "iv"
    assert ctx_3.transform("w") == "w"
    assert get_value_default(ctx_3) == "v"

    args_x = "x A,B%(.:/ik),c=C%(*:/ik)"
    ctx_4 = ItemGetValueContext(item, remaining_path, args_x, value, mapper,
                                {})
    assert ctx_4.substitute_and_transform("${.:/ik}") == "iv/A/Biv/Civ"
    assert ctx_4.transform("w") == "w/A/Biv/Civ"


def test_unpack_arg():
    arg = unpack_arg("\\0\\a\\b\\c\\f\\n\\r\\s\\t\\v\\%\\(\\)\\\\\\?%()\\x")
    assert arg == "\0\a\b,\f\n\r \t\v%()\\?${}x"


def test_unpack_args():

    def _substitute(text):
        return f"<{text}>"

    args, kwargs = unpack_args("a,b=c,d", _substitute)
    assert args == ["<a>", "<d>"]
    assert kwargs == {"b": "<c>"}

    assert unpack_args(None, _substitute) == ([], {})
