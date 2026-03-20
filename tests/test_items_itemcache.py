# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the items module. """

# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
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

import os
import pytest

from specitems.items import (EmptyItem, EmptyItemCache, ItemCache,
                             ItemCacheConfig, ItemSelection, ItemView,
                             SpecTypeProvider, item_is_enabled)

from .util import create_item_cache_config, get_other_type_data_by_uid


def test_add_remove_item():
    item_cache = EmptyItemCache()
    item_cache.add_item("/a", {"enabled-by": True, "links": [], "a": "a"})
    item_cache.add_item("/b", {
        "enabled-by": True,
        "links": [{
            "role": "b",
            "uid": "a"
        }],
        "b": "b"
    })
    item_cache.add_item("/c", {
        "enabled-by": True,
        "links": [{
            "role": "c",
            "uid": "b"
        }],
        "c": "c"
    })
    a = item_cache["/a"]
    b = item_cache["/b"]
    c = item_cache["/c"]
    assert a in item_cache.items_by_type[a.type]
    assert b in item_cache.items_by_type[b.type]
    assert c in item_cache.items_by_type[c.type]
    assert a["a"] == "a"
    assert b["b"] == "b"
    assert c["c"] == "c"
    assert a.child("b") == b
    assert b.parent("b") == a
    assert b.child("c") == c
    assert c.parent("c") == b
    item_cache.remove_item("/b")
    assert "/b" not in item_cache
    assert a in item_cache.items_by_type[a.type]
    assert b not in item_cache.items_by_type[b.type]
    assert c in item_cache.items_by_type[c.type]
    with pytest.raises(IndexError):
        assert a.child("b")
    with pytest.raises(IndexError):
        assert c.parent("c")
    b = item_cache.add_item("/b", b.data)
    with pytest.raises(IndexError):
        assert b.child("c") == c
    item_cache.reinitialize_links()
    assert b.child("c") == c


def _get_missing(item):
    return item.uid


def test_load(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache")
    config.enabled_set = ["foobar"]

    item_cache = ItemCache(config)
    assert item_cache.enabled_set == {"foobar"}
    assert len(item_cache.types) == 1
    assert list(item_cache.types)[0] == ""
    assert list(item.uid for item in sorted(item_cache.items_by_type[""])) == [
        "/c", "/d/c", "/p", "/proxy-member-default", "/q", "/r", "/s"
    ]
    cache_dir = config.cache_directory
    assert os.path.exists(os.path.join(cache_dir, "rel", "spec",
                                       "spec.pickle"))
    assert os.path.exists(
        os.path.join(cache_dir, "rel", "spec", "d", "spec.pickle"))
    dc = item_cache["/d/c"]
    assert dc["v"] == "c"
    assert item_cache["/p"]["v"] == "p"
    p = item_cache["/p"]
    assert not p.enabled
    selection = ItemSelection(item_cache, [], item_is_enabled)
    assert selection.is_enabled("/p")
    with item_cache.selection(selection):
        assert p.enabled
    assert p.is_enabled(["blub"])
    assert p["v"] == "p"
    assert p.map("/p") == p
    assert p.map("p") == p
    assert len(item_cache) == 7
    assert item_cache["/p"]["v"] == "p"
    assert item_cache["/d/c"]["v"] == "c"
    selection = ItemSelection(item_cache, [])
    item_cache.set_selection(selection)
    assert item_cache.enabled_set == set()
    assert item_cache.active_selection.enabled_set == set()
    assert p.enabled
    selection.reset(["foobar"])
    assert item_cache.enabled_set == {"foobar"}
    assert not p.enabled
    selection.extend_enabled_set(["foo", "foobar"])
    selection.extend_enabled_set("bar")
    assert item_cache.enabled_set == {"foobar", "foo", "bar"}
    assert not p.enabled
    selection.enabled_set = ["foobar"]
    assert item_cache.enabled_set == {"foobar"}
    assert not p.enabled
    selection.remove_from_enabled_set("foo")
    selection.remove_from_enabled_set(["bar", "foobar"])
    assert item_cache.enabled_set == set()
    assert p.enabled
    selection.apply_action({
        "action": "add",
        "enabled-by": True,
        "value": "foo"
    })
    assert item_cache.enabled_set == {"foo"}
    selection.apply_action({
        "action": "add",
        "enabled-by": True,
        "value": ["bar", "buh"]
    })
    assert item_cache.enabled_set == {"foo", "bar", "buh"}
    selection_2 = selection.clone(item_cache)
    assert selection_2.enabled_set == {"foo", "bar", "buh"}
    selection.apply_action({
        "action": "remove",
        "enabled-by": True,
        "value": ["bar", "buh"]
    })
    assert item_cache.enabled_set == {"foo"}
    selection.apply_action({
        "action": "add",
        "enabled-by": False,
        "value": "bar"
    })
    assert item_cache.enabled_set == {"foo"}
    selection.apply_action({
        "action": "remove",
        "enabled-by": True,
        "value": "foo"
    })
    assert item_cache.enabled_set == set()
    selection.apply_action({
        "action": "set",
        "enabled-by": True,
        "value": "xyz"
    })
    assert item_cache.enabled_set == {"xyz"}
    selection.apply_action({"action": "set", "enabled-by": True, "value": []})
    assert item_cache.enabled_set == set()
    assert selection_2.enabled_set == {"foo", "bar", "buh"}

    p.view["abc"] = 123
    p.view["cba"] = 321
    dc.view["def"] = "ghi"
    with item_cache.view_scope(ItemView()):
        with pytest.raises(KeyError):
            p.view["abc"]
        item_cache.view.add_get_missing("abc", _get_missing)
        p.view["abc"] = "/p"
        p.view["abc"] = 456
        dc.view["def"] = "klm"
        assert p.view["abc"] == 456
        assert dc.view["def"] == "klm"
        assert item_cache.top_view[p]["abc"] == 123
    assert p.view["abc"] == 123
    assert dc.view["def"] == "ghi"
    with item_cache.view_scope(ItemView(item_cache.view)):
        item_cache.view.add_get_missing("cba", _get_missing)
        assert p.view["abc"] == 123
        p.view["abc"] = 456
        assert p.view["abc"] == 456
        assert p.view.get("abc") == 456
        assert p.view.get("cba") == "/p"
        assert p.view.get("xyz") == None
    assert p.view["abc"] == 123

    item_cache_2 = ItemCache(config)
    assert item_cache_2["/d/c"]["v"] == "c"
    with open(os.path.join(tmpdir, "spec", "d", "c.yml"), "w+") as out:
        out.write("""enabled-by: true
links:
- role: ''
  uid: ../p
v: x""")

    item_cache_3 = ItemCache(config)
    assert item_cache_3["/d/c"]["v"] == "x"
    item = item_cache_3.add_item_from_file(
        "/foo/bar",
        os.path.join(os.path.dirname(__file__), "spec-item-cache/r.yml"))
    assert item.uid == "/foo/bar"
    assert item.type == ""
    assert item["type"] == "other"
    os.remove(os.path.join(tmpdir, "spec", "d", "c.yml"))
    item_cache_4 = ItemCache(config)
    with pytest.raises(KeyError):
        item_cache_4["/d/c"]


def test_item_type_provider():
    item_cache = EmptyItemCache(SpecTypeProvider(get_other_type_data_by_uid()))
    match = r"item /no-type has no type attribute 'type' for partial type ''"
    with pytest.raises(ValueError, match=match):
        item_cache.add_item("/no-type", {"enabled-by": True, "links": []})
    match = r"item /invalid-type has invalid type refinement 'invalid' for partial type 'invalid'"
    with pytest.raises(ValueError, match=match):
        item_cache.add_item("/invalid-type", {
            "enabled-by": True,
            "links": [],
            "type": "invalid"
        })
    no_type = item_cache.add_item("/no-type", {
        "enabled-by": True,
        "links": []
    }, False, False)
    assert no_type.type == ""

    item_cache.type_provider.permissive_type_errors = True

    no_type_2 = item_cache.add_item("/no-type-2", {
        "enabled-by": True,
        "links": []
    })
    assert no_type.type == ""

    invalid_type = item_cache.add_item("/invalid-type", {
        "enabled-by": True,
        "links": [],
        "type": "invalid"
    })
    assert invalid_type.type == "invalid"


def _parents(item):
    return list((link.item.uid, link.role) for link in item.links_to_parents())


def _children(item):
    return list(
        (link.item.uid, link.role) for link in item.links_to_children())


def test_proxy(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache")
    item_cache = ItemCache(config)
    p = item_cache["/p"]
    s = item_cache["/s"]
    proxy_member_default = item_cache["/proxy-member-default"]
    assert item_cache["/proxy"] is p
    proxy2 = item_cache["/proxy2"]
    assert proxy2.is_proxy()
    proxy2.init_parents(item_cache)
    item_cache.type_provider.set_type(proxy2)

    # Proxy member parents may be a bit surprising
    assert _parents(p) == [("/p", "proxy-member")]
    assert _children(p) == [("/d/c", "")]
    assert _parents(s) == [("/proxy2", "proxy-member"), ("/r", "xyz")]
    assert _children(s) == [("/c", "oops")]
    assert _parents(proxy_member_default) == [
        ("/p", "proxy-member-default"),
        ("/proxy2", "proxy-member-default"),
        ("/r", "xyz"),
    ]
    assert _children(proxy_member_default) == [("/c", "oops")]
    assert _parents(proxy2) == []
    assert _children(proxy2) == [("/c", "oops")]

    item_cache.active_selection.reset(["foobar"])

    proxy = item_cache["/proxy"]
    assert proxy.is_proxy()

    assert item_cache["/proxy2"] is s
    item_cache.resolve_proxies = False
    assert item_cache["/proxy2"] is proxy2
    item_cache.resolve_proxies = True

    assert _parents(p) == [("/proxy", "proxy-member")]
    assert _parents(s) == [("/s", "proxy-member"), ("/r", "xyz")]
    assert _parents(proxy_member_default) == [
        ("/proxy", "proxy-member-default"),
        ("/s", "proxy-member-default"),
        ("/r", "xyz"),
    ]
    assert _parents(proxy) == []
    assert _children(proxy) == []
    assert _parents(proxy2) == []

    item_cache.active_selection.reset(["foobar", "proxy-member-default"])

    assert item_cache["/proxy"] is proxy_member_default
    assert item_cache["/proxy2"] is s

    assert _parents(p) == [("/proxy-member-default", "proxy-member")]
    assert _parents(s) == [("/s", "proxy-member"), ("/r", "xyz")]
    assert _parents(proxy_member_default) == [
        ("/proxy-member-default", "proxy-member-default"),
        ("/s", "proxy-member-default"),
        ("/r", "xyz"),
    ]
    assert _parents(proxy) == []
    assert _parents(proxy2) == []

    item_cache.active_selection.reset(["proxy-member-default"])

    assert item_cache["/proxy"] is p
    assert item_cache["/proxy2"] is proxy_member_default

    assert _parents(p) == [("/p", "proxy-member")]
    assert _parents(s) == [
        ("/proxy-member-default", "proxy-member"),
        ("/r", "xyz"),
    ]
    assert _parents(proxy_member_default) == [
        ("/p", "proxy-member-default"),
        ("/proxy-member-default", "proxy-member-default"),
        ("/r", "xyz"),
    ]
    assert _parents(proxy) == []
    assert _parents(proxy2) == []


def test_proxy_reinitialize_links(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache")
    config.initialize_links = False
    item_cache = ItemCache(config)
    item_cache.reinitialize_links()
    p = item_cache["/p"]
    s = item_cache["/s"]
    proxy_member_default = item_cache["/proxy-member-default"]
    assert item_cache["/proxy"] is p
    proxy2 = item_cache["/proxy2"]
    assert proxy2.is_proxy()

    # Proxy member parents may be a bit surprising
    assert _parents(p) == [("/p", "proxy-member")]
    assert _children(p) == [("/d/c", "")]
    assert _parents(s) == [("/proxy2", "proxy-member"), ("/r", "xyz")]
    assert _children(s) == [("/c", "oops")]
    assert _parents(proxy_member_default) == [
        ("/p", "proxy-member-default"),
        ("/proxy2", "proxy-member-default"),
        ("/r", "xyz"),
    ]
    assert _children(proxy_member_default) == [("/c", "oops")]
    assert _parents(proxy2) == []
    assert _children(proxy2) == [("/c", "oops")]


def test_load_yaml_abs(tmpdir):
    config = ItemCacheConfig()
    spec_dir = os.path.join(os.path.dirname(__file__), "spec-item-cache")
    item_cache = ItemCache(config)
    item_cache.load_items(spec_dir, True, True)
    assert item_cache["/c"]["v"] == "c"
    item_cache_2 = ItemCache(config)
    item_cache_2.load_items(spec_dir, True, True, "yaml")
    assert item_cache_2["/c"]["v"] == "c"


def test_load_uid_prefix(tmpdir):
    spec_dir = os.path.join(os.path.dirname(__file__), "spec-item-cache")
    config = ItemCacheConfig(paths={spec_dir: "/prefix/"},
                             cache_directory=os.path.join(tmpdir, "cache"))
    item_cache = ItemCache(config)
    assert item_cache["/prefix/c"]["v"] == "c"
    config.paths = []
    item_cache_2 = ItemCache(config)
    item_cache_2.load_items((spec_dir, "/prefix/"), True, True)
    assert item_cache_2["/prefix/c"]["v"] == "c"


def test_load_link_error(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache-2")
    config.initialize_links = False
    item_cache = ItemCache(config)
    match = r"item /b links to non-existing item 'nix' through proxy /a"
    with pytest.raises(KeyError, match=match):
        item_cache.add_item("/b", {
            "enabled-by": True,
            "links": [{
                "role": "proxy-member",
                "uid": "a"
            }]
        })
    config.initialize_links = True
    match = r"item /x links to non-existing item 'nix'"
    with pytest.raises(KeyError, match=match):
        ItemCache(config)


def test_load_yaml_error(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-item-cache-3")
    match = r"YAML error while loading specification item file '.*invalid.yml': while parsing a block mapping"
    with pytest.raises(IOError, match=match):
        ItemCache(config)
