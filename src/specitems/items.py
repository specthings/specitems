# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a specification item representation organized in an item cache.
"""

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

# pylint: disable=too-many-lines

from contextlib import contextmanager
import base64
import dataclasses
import hashlib
import itertools
import os
import pickle
import re
import stat
from typing import (Any, Callable, Collection, Iterable, Iterator, Match,
                    Optional, Union)
import json
import yaml

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader  # type: ignore

ItemDataByUID = dict[str, dict[str, dict]]
EnabledSet = Collection[str]
IsEnabled = Callable[[EnabledSet, "Item"], bool]
IsLinkEnabled = Callable[["Link"], bool]
ItemViewGetMissing = Callable[["Item"], Any]


class _DirectView(dict):

    def __init__(self, item: "Item",
                 get_missing_map: dict[str, ItemViewGetMissing]) -> None:
        super().__init__()
        self._item = item
        self._get_missing_map = get_missing_map

    def __missing__(self, key):
        return self._get_missing_map[key](self._item)


class _InheritanceView(dict):

    def __init__(self, item: "Item", get_missing_map: dict[str,
                                                           ItemViewGetMissing],
                 view: "ItemView") -> None:
        super().__init__()
        self._item = item
        self._get_missing_map = get_missing_map
        self._view = view

    def __missing__(self, key):
        get_missing = self._get_missing_map.get(key, None)
        if get_missing is None:
            value = self._view[self._item][key]
        else:
            value = get_missing(self._item)
        self[key] = value
        return value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


class ItemView(dict):
    """
    Provides a view of the specification items.

    Item views can be pushed to and popped from an item cache.  They provide a
    context-specific view to the items.  For example, a package may contain
    several components.  Each component may use its own view to the items.
    """

    def __init__(self, view: Optional["ItemView"] = None) -> None:
        super().__init__()
        self._view = view
        self._get_missing_map: dict[str, ItemViewGetMissing] = {}

    def __missing__(self, item: "Item") -> dict:
        if self._view is None:
            new_dict: dict = _DirectView(item, self._get_missing_map)
        else:
            new_dict = _InheritanceView(item, self._get_missing_map,
                                        self._view)
        return self.setdefault(item, new_dict)

    def add_get_missing(self, key: str,
                        get_missing: ItemViewGetMissing) -> None:
        """ Add the get missing method for the key. """
        self._get_missing_map[key] = get_missing


def _is_enabled_op_and(enabled_set: EnabledSet, enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if not is_enabled(enabled_set, next_enabled_by):
            return False
    return True


def _is_enabled_op_not(enabled_set: EnabledSet, enabled_by: Any) -> bool:
    return not is_enabled(enabled_set, enabled_by)


def _is_enabled_op_or(enabled_set: EnabledSet, enabled_by: Any) -> bool:
    for next_enabled_by in enabled_by:
        if is_enabled(enabled_set, next_enabled_by):
            return True
    return False


_IS_ENABLED_OP = {
    "and": _is_enabled_op_and,
    "not": _is_enabled_op_not,
    "or": _is_enabled_op_or
}


def is_enabled(enabled_set: EnabledSet, enabled_by: Any) -> bool:
    """ Evaluate the enabled-by expression using the enabled set. """
    if isinstance(enabled_by, bool):
        return enabled_by
    if isinstance(enabled_by, list):
        return _is_enabled_op_or(enabled_set, enabled_by)
    if isinstance(enabled_by, dict):
        key, value = next(iter(enabled_by.items()))
        return _IS_ENABLED_OP[key](enabled_set, value)
    return enabled_by in enabled_set


def _ops_is_enabled_op_and(enabled_set: EnabledSet, enabled_by: Any,
                           ops: dict) -> bool:
    for next_enabled_by in enabled_by:
        if not is_enabled_with_ops(enabled_set, next_enabled_by, ops):
            return False
    return True


def _ops_is_enabled_op_not(enabled_set: EnabledSet, enabled_by: Any,
                           ops: dict) -> bool:
    return not is_enabled_with_ops(enabled_set, enabled_by, ops)


def _ops_is_enabled_op_or(enabled_set: EnabledSet, enabled_by: Any,
                          ops: dict) -> bool:
    for next_enabled_by in enabled_by:
        if is_enabled_with_ops(enabled_set, next_enabled_by, ops):
            return True
    return False


IS_ENABLED_OPS = {
    "and": _ops_is_enabled_op_and,
    "not": _ops_is_enabled_op_not,
    "or": _ops_is_enabled_op_or
}


def is_enabled_with_ops(enabled_set: EnabledSet, enabled_by: Any,
                        ops: dict) -> bool:
    """
    Evaluate the enabled-by expression using the enabled set with custom
    operations.
    """
    if isinstance(enabled_by, bool):
        return enabled_by
    if isinstance(enabled_by, list):
        return _ops_is_enabled_op_or(enabled_set, enabled_by, ops)
    if isinstance(enabled_by, dict):
        key, value = next(iter(enabled_by.items()))
        return ops[key](enabled_set, value, ops)
    return enabled_by in enabled_set


def _str_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str",
                                   data,
                                   style="|" if "\n" in data else "")


yaml.add_representer(str, _str_representer)


class Link:
    """ Represents a link to an item. """

    def __init__(self, item: "Item", data: dict) -> None:
        self._item = item
        self._uid = item.uid
        self.data = data

    def __getitem__(self, name: str) -> Any:
        return self.data[name]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self._uid == other._uid

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Link):
            return NotImplemented
        return self._uid < other._uid

    @property
    def role(self) -> str:
        """ Is the link role. """
        return self.data["role"]

    @property
    def item(self) -> "Item":
        """ Is the link item. """
        return self._item

    @property
    def uid(self) -> str:
        """ Is the link item UID. """
        return self._uid


class _ProxyLink(Link):

    @property
    def item(self) -> "Item":
        return self._item.cache[self._uid]


_TYPES = {
    type(True): "B".encode("utf-8"),
    type(1.0): "F".encode("utf-8"),
    type(1): "I".encode("utf-8"),
    type(None): "N".encode("utf-8"),
    type(""): "S".encode("utf-8"),
}


def _hash_data(data, state) -> None:
    if isinstance(data, list):
        for value in data:
            _hash_data(value, state)
    elif isinstance(data, dict):
        for key, value in sorted(data.items()):
            state.update(str(key).encode("utf-8"))
            _hash_data(value, state)
    else:
        state.update(_TYPES[type(data)])
        state.update(str(data).encode("utf-8"))


def data_digest(data: dict) -> str:
    """ Return the digest of the data. """
    state = hashlib.sha256()
    _hash_data(data, state)
    return base64.urlsafe_b64encode(state.digest()).decode("ascii")


_UID_TO_UPPER = re.compile(r"[/_-]+(.)")


def _match_to_upper(match: Match) -> str:
    return match.group(1).upper()


def _is_link_enabled(link: Link) -> bool:
    return link.item.enabled


def link_is_enabled(_link: Link) -> bool:
    """ Return true. """
    return True


def _yield_links(links: Iterable[Link], role: Optional[Union[str,
                                                             Iterable[str]]],
                 is_link_enabled: IsLinkEnabled) -> Iterator[Link]:
    if role is None:
        for link in links:
            if is_link_enabled(link):
                yield link
    elif isinstance(role, str):
        for link in links:
            if link.role == role and is_link_enabled(link):
                yield link
    else:
        for link in links:
            if link.role in role and is_link_enabled(link):
                yield link


class Item:
    """ Represents a specification item. """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods
    def __init__(self, item_cache: "ItemCache", uid: str, data: dict) -> None:
        self.data = data
        self.file: str = data.pop("_file", os.devnull)
        self.type = ""
        self._cache = item_cache
        self._ident = _UID_TO_UPPER.sub(_match_to_upper, uid)
        self._uid = uid
        self._links_to_parents: list[Link] = []
        self._links_to_children: list[Link] = []

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return self._uid == other._uid  # pylint: disable=protected-access

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Item):
            return NotImplemented
        return self._uid < other._uid  # pylint: disable=protected-access

    def __hash__(self) -> int:
        return hash(self._uid)

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    @property
    def enabled(self) -> bool:
        """ Is true, if the item is enabled, otherwise is false. """
        return self.cache.is_enabled(self.uid)

    @property
    def cache(self) -> "ItemCache":
        """ Is the cache of the item. """
        return self._cache

    @property
    def view(self) -> dict:
        """ Is the active item view. """
        return self._cache.view[self]

    @property
    def digest(self) -> str:
        """ Return the digest of the item data. """
        return data_digest(self.data)

    @property
    def uid(self) -> str:
        """ Is the UID of the item. """
        return self._uid

    @property
    def ident(self) -> str:
        """ Is the identifier of the item. """
        return self._ident

    @property
    def spec(self) -> str:
        """ Is the UID of the item with an URL-like format. """
        return f"spec:{self.uid}"

    @property
    def spec_2(self) -> str:
        """
        Is the UID of the item with an URL-like format with invisible white
        space to allow line breaks.
        """
        uid = self.uid.replace("/", "/\u200b")
        return f"spec:{uid}"

    def get(self, key: str, default: Any) -> Any:
        """
        Get the attribute value if the attribute exists, otherwise the
        specified default value is returned.
        """
        return self.data.get(key, default)

    def to_abs_uid(self, abs_or_rel_uid: str) -> str:
        """
        Return the absolute UID of an absolute UID or an UID relative to this
        item.
        """
        if abs_or_rel_uid == ".":
            return self.uid
        if os.path.isabs(abs_or_rel_uid):
            return abs_or_rel_uid
        return os.path.normpath(
            os.path.join(os.path.dirname(self.uid), abs_or_rel_uid))

    def map(self, abs_or_rel_uid: str) -> "Item":
        """
        Map the absolute UID or the UID relative to this item to the
        corresponding item.
        """
        return self._cache[self.to_abs_uid(abs_or_rel_uid)]

    def links_to_parents(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            is_link_enabled: IsLinkEnabled = _is_link_enabled
    ) -> Iterator[Link]:
        """ Yield the links to the parents of this item. """
        yield from _yield_links(self._links_to_parents, role, is_link_enabled)

    def parents(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            is_link_enabled: IsLinkEnabled = _is_link_enabled
    ) -> Iterator["Item"]:
        """ Yield the parents of this item. """
        for link in self.links_to_parents(role, is_link_enabled):
            yield link.item

    def parent(self,
               role: Optional[Union[str, Iterable[str]]] = None,
               index: Optional[int] = 0,
               is_link_enabled: IsLinkEnabled = _is_link_enabled) -> "Item":
        """ Return the parent with the specified role and index. """
        for item_index, item in enumerate(self.parents(role, is_link_enabled)):
            if item_index == index:
                return item
        raise IndexError

    def parent_link(self,
                    role: Optional[Union[str, Iterable[str]]] = None,
                    index: Optional[int] = 0,
                    is_link_enabled: IsLinkEnabled = _is_link_enabled) -> Link:
        """ Return the parent link with the specified role and index. """
        for link_index, link in enumerate(
                self.links_to_parents(role, is_link_enabled)):
            if link_index == index:
                return link
        raise IndexError

    def links_to_children(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            is_link_enabled: IsLinkEnabled = _is_link_enabled
    ) -> Iterator[Link]:
        """ Yield the links to the children of this item. """
        yield from _yield_links(self._links_to_children, role, is_link_enabled)

    def children(
            self,
            role: Optional[Union[str, Iterable[str]]] = None,
            is_link_enabled: IsLinkEnabled = _is_link_enabled
    ) -> Iterator["Item"]:
        """ Yield the children of this item. """
        for link in self.links_to_children(role, is_link_enabled):
            yield link.item

    def child(self,
              role: Optional[Union[str, Iterable[str]]] = None,
              index: Optional[int] = 0,
              is_link_enabled: IsLinkEnabled = _is_link_enabled) -> "Item":
        """ Return the child with the specified role and index. """
        for item_index, item in enumerate(self.children(role,
                                                        is_link_enabled)):
            if item_index == index:
                return item
        raise IndexError

    def child_link(self,
                   role: Optional[Union[str, Iterable[str]]] = None,
                   index: Optional[int] = 0,
                   is_link_enabled: IsLinkEnabled = _is_link_enabled) -> Link:
        """ Return the child link with the specified role and index. """
        for link_index, link in enumerate(
                self.links_to_children(role, is_link_enabled)):
            if link_index == index:
                return link
        raise IndexError

    def init_parents(self, item_cache: "ItemCache") -> None:
        """ Initialize the list of links to parents of this item. """
        # pylint: disable=protected-access
        proxies = item_cache.proxies
        for data in self.data["links"]:
            uid = self.to_abs_uid(data["uid"])
            parent = proxies.get(uid)
            if parent is None:
                try:
                    parent = item_cache[uid]
                except KeyError as err:
                    msg = (f"item {self._uid} links "
                           f"to non-existing item '{data['uid']}'")
                    raise KeyError(msg) from err
                self._links_to_parents.append(Link(parent, data))
            else:
                self._links_to_parents.append(_ProxyLink(parent, data))
            parent._links_to_children.append(Link(self, data))
            if data["role"].startswith("proxy-member"):
                for data_2 in parent.data["links"]:
                    try:
                        parent_2 = item_cache[parent.to_abs_uid(data_2["uid"])]
                    except KeyError as err:
                        msg = (f"item {self._uid} links "
                               f"to non-existing item '{data_2['uid']}' "
                               f"through proxy {parent._uid}")
                        raise KeyError(msg) from err
                    self._links_to_parents.append(Link(parent_2, data_2))
                    parent_2._links_to_children.append(Link(self, data_2))

    def init_children(self) -> None:
        """ Initialize the list of links to children of this item. """
        self._links_to_children.sort()

    def clear_links(self) -> None:
        """ Clear the links of this item. """
        # pylint: disable=protected-access
        for link in self._links_to_parents:
            # It is necessary to directly use the internal "_item" member to
            # avoid a proxy resolution.
            link._item._links_to_children.remove(Link(self, link.data))
        for link in self._links_to_children:
            try:
                link.item._links_to_parents.remove(Link(self, link.data))
            except ValueError:
                # If the item is a proxy member, then the parent link may
                # actually reference the proxy item.
                pass
        self._links_to_parents = []
        self._links_to_children = []

    def add_link_to_parent(self, link: Link):
        """ Add the link as a parent item link to this item. """
        self._links_to_parents.append(link)

    def add_link_to_child(self, link: Link):
        """ Add the link as a child item link to this item. """
        self._links_to_children.append(link)

    def is_enabled(self, enabled_set: EnabledSet) -> bool:
        """
        Return true, if the item is enabled for the enabled set, otherwise
        return false.
        """
        return is_enabled(enabled_set, self.data["enabled-by"])

    def is_proxy(self) -> bool:
        """ Returns true, if the item is a proxy, otherwise false. """
        return False

    def save(self) -> None:
        """ Saves the item to the corresponding file. """
        save_data(self.file, self.data)

    def load(self) -> None:
        """ Loads the item from the corresponding file. """
        self.data = load_data(self.file)


class _ProxyItem(Item):

    def __init__(self, item_cache: "ItemCache", uid: str, data: dict) -> None:
        super().__init__(item_cache, uid, data)
        self.type = "proxy"

    def is_proxy(self) -> bool:
        return True

    def init_parents(self, item_cache: "ItemCache") -> None:
        pass

    def init_children(self) -> None:
        # pylint: disable=protected-access
        members: list[Item] = []
        others: list[tuple[Item, Any]] = []
        for link in self._links_to_children:
            if link.role.startswith("proxy-member"):
                members.append(link.item)
            else:
                others.append((link.item, link.data))
        for member in members:
            for other, data in others:
                member._links_to_children.append(Link(other, data))
            member._links_to_children.sort()


def create_unique_link(child: Item, parent: Item, data: dict) -> None:
    """
    Create a unique link from the child to the parent item and vice versa
    using the data for the link.
    """
    for item in parent.children(data["role"], is_link_enabled=link_is_enabled):
        if item.uid == child.uid:
            break
    else:
        parent.add_link_to_child(Link(child, data))
        child.add_link_to_parent(Link(parent, data))


def _json_load_data(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as src:
        try:
            data = json.load(src)
        except json.JSONDecodeError as err:
            msg = ("JSON error while loading specification item file "
                   f"'{path}': {str(err)}")
            raise IOError(msg) from err
        data["_file"] = os.path.abspath(path)
    return data


def _json_load_data_by_uid(data_by_uid: ItemDataByUID, _cache_dir: str,
                           uid_prefix: str, base: str, path: str) -> None:
    for name in sorted(os.listdir(path)):
        path_2 = os.path.join(path, name)
        if name.endswith(".json") and not name.startswith("."):
            uid = uid_prefix + os.path.relpath(path_2, base).replace(
                ".json", "")
            data_by_uid[uid] = _json_load_data(path_2)
        elif stat.S_ISDIR(os.lstat(path_2).st_mode):
            _json_load_data_by_uid(data_by_uid, _cache_dir, uid_prefix, base,
                                   path_2)


def _json_save_data(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as out:
        json.dump(data, out, sort_keys=True, indent=2)


def _yaml_load_data(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as src:
        try:
            data: dict = yaml.load(src.read(), Loader=SafeLoader)
        except yaml.YAMLError as err:
            msg = ("YAML error while loading specification item file "
                   f"'{path}': {str(err)}")
            raise IOError(msg) from err
        data["_file"] = os.path.abspath(path)
    return data


def _yaml_save_data(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as out:
        out.write(yaml.dump(data, default_flow_style=False,
                            allow_unicode=True))


def _yaml_load_items_in_dir(data_by_uid: ItemDataByUID, cache_file: str,
                            uid_prefix: str, base: str, path: str) -> None:
    data_by_uid_2: dict[str, dict] = {}
    for name in sorted(os.listdir(path)):
        path_2 = os.path.join(path, name)
        if name.endswith(".yml") and not name.startswith("."):
            uid = uid_prefix + os.path.relpath(path_2, base).replace(
                ".yml", "")
            data_by_uid_2[uid] = _yaml_load_data(path_2)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "wb") as out:
        pickle.dump(data_by_uid_2, out)
    data_by_uid.update(data_by_uid_2)


def _yaml_load_data_by_uid(data_by_uid: ItemDataByUID, cache_dir: str,
                           uid_prefix: str, base: str, path: str) -> None:
    root_dir = os.path.normpath(os.path.dirname(cache_dir))
    common_path = os.path.normpath(os.path.commonpath([root_dir, path]))
    if root_dir == common_path:
        cache_file = os.path.join(cache_dir, "rel",
                                  os.path.relpath(path, root_dir),
                                  "spec.pickle")
    else:
        cache_file = os.path.join(cache_dir, "abs", os.path.relpath(path, "/"),
                                  "spec.pickle")
    try:
        mtime = os.path.getmtime(cache_file)
        update_cache = False
    except FileNotFoundError:
        update_cache = True
    else:
        update_cache = mtime <= os.path.getmtime(path)
    for name in sorted(os.listdir(path)):
        path_2 = os.path.join(path, name)
        if name.endswith(".yml") and not name.startswith("."):
            if not update_cache:
                update_cache = mtime <= os.path.getmtime(path_2)
        elif stat.S_ISDIR(os.lstat(path_2).st_mode):
            _yaml_load_data_by_uid(data_by_uid, cache_dir, uid_prefix, base,
                                   path_2)
    if update_cache:
        _yaml_load_items_in_dir(data_by_uid, cache_file, uid_prefix, base,
                                path)
    else:
        with open(cache_file, "rb") as src:
            data_by_uid.update(pickle.load(src))


_LOAD_DATA_BY_UID = {
    "json": _json_load_data_by_uid,
    "yaml": _yaml_load_data_by_uid
}

_LOAD_DATA = {"json": _json_load_data, "yaml": _yaml_load_data}

_SAVE_DATA = {"json": _json_save_data, "yaml": _yaml_save_data}

_EXT_TO_FORMAT = {".json": "json", ".yaml": "yaml", ".yml": "yaml"}


def _get_format(path: str) -> str:
    return _EXT_TO_FORMAT[os.path.splitext(path)[1]]


def load_data(path: str) -> dict:
    """ Load the item data from the file specified by path. """
    return _LOAD_DATA[_get_format(path)](path)


def save_data(path: str, data: dict) -> None:
    """ Save the item data to the file specified by path. """
    _SAVE_DATA[_get_format(path)](path,
                                  dict((key, value)
                                       for key, value in sorted(data.items())))


def load_data_by_uid(path: str, cache_dir: str, uid_prefix: str,
                     the_format: str) -> ItemDataByUID:
    """
    Load the data by UID from the path using the cache directory and files of
    the format.
    """
    data_by_uid: ItemDataByUID = {}
    path = os.path.abspath(path)
    _LOAD_DATA_BY_UID[the_format](data_by_uid, cache_dir, uid_prefix, path,
                                  path)
    return data_by_uid


def pickle_load_data_by_uid(pickle_file: str) -> ItemDataByUID:
    """ Load the data by UID from the pickle file. """
    with open(pickle_file, "rb") as src:
        return pickle.load(src)


def _is_item_enabled(enabled_set: EnabledSet, item: Item) -> bool:
    return is_enabled(enabled_set, item["enabled-by"])


def item_is_enabled(_enabled_set: EnabledSet, _item: Item) -> bool:
    """ Return true. """
    return True


def to_collection(value: str | Collection[str]) -> Collection[str]:
    """
    Convert the value to a single element collection if it is a string.
    """
    if isinstance(value, str):
        return (value, )
    return value


def to_iterable(value: str | Iterable[str]) -> Iterable[str]:
    """
    Convert the value to a single element iterable if it is a string.
    """
    if isinstance(value, str):
        return (value, )
    return value


def _enabled_set_add(selection: "ItemSelection",
                     value: str | EnabledSet) -> None:
    selection.extend_enabled_set(value)


def _enabled_set_remove(selection: "ItemSelection",
                        value: str | EnabledSet) -> None:
    selection.remove_from_enabled_set(value)


def _enabled_set_set(selection: "ItemSelection",
                     value: str | EnabledSet) -> None:
    selection.enabled_set = to_collection(value)


_ENABLED_SET_ACTIONS = {
    "add": _enabled_set_add,
    "remove": _enabled_set_remove,
    "set": _enabled_set_set
}


class ItemSelection(dict):
    """ Determines which specification items are enabled in an item cache. """

    def __init__(self,
                 item_cache: "ItemCache",
                 enabled_set: Iterable[str],
                 is_item_enabled: IsEnabled = _is_item_enabled):
        self.cache = item_cache
        self._enabled_set = frozenset(enabled_set)
        self._is_item_enabled = is_item_enabled

    def clone(self, item_cache: "ItemCache") -> "ItemSelection":
        """ Clones the item selection. """
        return ItemSelection(item_cache, self._enabled_set,
                             self._is_item_enabled)

    @property
    def enabled_set(self) -> EnabledSet:
        """ Is the enabled set. """
        return self._enabled_set

    @enabled_set.setter
    def enabled_set(self, enabled_set: EnabledSet) -> None:
        """ Set the enabled set. """
        self.clear()
        self._enabled_set = frozenset(enabled_set)

    def is_enabled(self, item: Item) -> bool:
        """
        Return true, if the item is enabled with respect to the item
        selection, otherwise return false.
        """
        return self._is_item_enabled(self._enabled_set, item)

    def extend_enabled_set(self, enabled_set: str | EnabledSet) -> None:
        """
        Extend the enabled set of the item selection with the members of the
        specified enabled set.
        """
        self.clear()
        self._enabled_set = frozenset(
            itertools.chain(self._enabled_set, to_iterable(enabled_set)))

    def remove_from_enabled_set(self, enabled_set: str | EnabledSet) -> None:
        """
        Remove all members of the specified enabled set from the enabled set
        of the item selection.
        """
        self.clear()
        self._enabled_set = frozenset(
            member for member in self._enabled_set
            if member not in to_collection(enabled_set))

    def apply_action(self, action: dict[str, Any]) -> None:
        """ Apply the action on the enabled set if enabled. """
        if is_enabled(self._enabled_set, action["enabled-by"]):
            _ENABLED_SET_ACTIONS[action["action"]](self, action["value"])

    def reset(self,
              enabled_set: EnabledSet,
              is_item_enabled: IsEnabled = _is_item_enabled) -> None:
        """
        Reset the item selection to use the new enabled set and method.
        """
        self.clear()
        self._enabled_set = frozenset(enabled_set)
        self._is_item_enabled = is_item_enabled

    def __missing__(self, uid: str) -> bool:
        return self.setdefault(
            uid, self._is_item_enabled(self._enabled_set, self.cache[uid]))


@dataclasses.dataclass
class ItemType:
    """
    Represents a specification type with its refinement key and the
    refinements.
    """
    key: Optional[str]
    refinements: dict[str, "ItemType"]


class ItemTypeProvider():
    """ Provides a type system for specification items. """

    def __init__(self, data_by_uid: ItemDataByUID,
                 spec_type_root_uid: Optional[str]) -> None:
        self.types: set[str] = set()
        self.items_by_type: dict[str, list[Item]] = {}
        self.root_type_uid = spec_type_root_uid
        self.data_by_uid: ItemDataByUID = {}
        self._type_refinements: dict[str, ItemType] = {}
        if spec_type_root_uid is None:
            self.root_type = ItemType(None, {})
        else:
            self.add_spec_types(data_by_uid)
            self.root_type = self._type_refinements[spec_type_root_uid]

    def set_type(self, item: Item) -> None:
        """ Set the type of the item. """
        if item.is_proxy():
            return
        spec_type = self.root_type
        value = item.data
        path: list[str] = []
        while spec_type.key is not None:
            try:
                type_name = value[spec_type.key]
            except KeyError as err:
                raise ValueError(
                    f"item {item.uid} has no type attribute "
                    f"'{spec_type.key}' for partial type '{'/'.join(path)}'"
                ) from err
            path.append(type_name)
            try:
                spec_type = spec_type.refinements[type_name]
            except KeyError as err:
                raise ValueError(
                    f"item {item.uid} has invalid type refinement "
                    f"'{type_name}' for partial type '{'/'.join(path)}'"
                ) from err
        the_type = "/".join(path)
        item.type = the_type
        self.types.add(the_type)
        self.items_by_type.setdefault(the_type, []).append(item)

    def add_spec_types(self, data_by_uid: ItemDataByUID) -> None:
        """ Add the specification types of the data by UID dictionary. """
        for uid, data in data_by_uid.items():
            if data.get("type", "") != "spec":
                continue
            for link in data["links"]:
                if link["role"] != "spec-refinement":
                    continue
                key = link["spec-key"]
                uid_2 = link["uid"]
                if not os.path.isabs(uid_2):
                    uid_2 = os.path.normpath(
                        os.path.join(os.path.dirname(uid), uid_2))
                spec_type = self._type_refinements.setdefault(
                    uid_2, ItemType(key, {}))
                if spec_type.key is None:
                    spec_type.key = key
                else:
                    assert spec_type.key == key
                spec_type.refinements[
                    link["spec-value"]] = self._type_refinements.setdefault(
                        uid, ItemType(None, {}))
        self.data_by_uid.update(data_by_uid)


class SpecTypeProvider(ItemTypeProvider):
    """ Provides a type system for default specification items. """

    def __init__(self, data_by_uid: ItemDataByUID) -> None:
        data_by_uid.update(
            pickle_load_data_by_uid(
                os.path.join(os.path.dirname(__file__), "spec.pickle")))
        super().__init__(data_by_uid, "/spec/root")


@dataclasses.dataclass
class ItemCacheConfig:
    """ Represents an item cache configuration. """
    enabled_set: list[str] = dataclasses.field(default_factory=list)
    paths: list[str] | dict[str, str] = dataclasses.field(default_factory=list)
    spec_type_root_uid: str | None = None
    initialize_links: bool = True
    resolve_proxies: bool = True
    cache_directory: str = "cache"


class ItemCache(dict):
    """ Provides a cache of specification items. """

    # pylint: disable=too-many-public-methods
    def __init__(self,
                 config: ItemCacheConfig,
                 is_item_enabled: IsEnabled = _is_item_enabled,
                 type_provider: ItemTypeProvider | None = None,
                 the_format: str = "yaml") -> None:
        super().__init__()
        self.resolve_proxies = config.resolve_proxies
        self.proxies: dict[str, Item] = {}
        self._format = the_format
        self._cache_directory: str = os.path.abspath(config.cache_directory)
        self._selection_stack = [
            ItemSelection(self, config.enabled_set, is_item_enabled)
        ]
        self._view_stack = [ItemView()]
        if type_provider is None:
            data_by_uid: ItemDataByUID = {}
        else:
            data_by_uid = type_provider.data_by_uid
        paths = config.paths
        if isinstance(paths, list):
            for path in paths:
                data_by_uid.update(
                    load_data_by_uid(path, self._cache_directory, "/",
                                     the_format))
        else:
            for path, uid_prefix in paths.items():
                data_by_uid.update(
                    load_data_by_uid(path, self._cache_directory, uid_prefix,
                                     the_format))
        self.add_items(data_by_uid, config.initialize_links, False)
        if type_provider is None:
            type_provider = ItemTypeProvider(data_by_uid,
                                             config.spec_type_root_uid)
        self.type_provider = type_provider
        for item in self.values():
            self.type_provider.set_type(item)

    def __missing__(self, uid: str) -> Item:
        proxy = self.proxies[uid]
        if self.resolve_proxies:
            for item in proxy.children("proxy-member"):
                return item
            for item in proxy.children("proxy-member-default"):
                return item
        return proxy

    @property
    def types(self) -> set[str]:
        """ Is the types of the items. """
        return self.type_provider.types

    @property
    def items_by_type(self) -> dict[str, list[Item]]:
        """ Is the set of items by type. """
        return self.type_provider.items_by_type

    @property
    def enabled_set(self) -> EnabledSet:
        """ Is the enabled set of the active item selection. """
        return self._selection_stack[-1].enabled_set

    @property
    def active_selection(self) -> ItemSelection:
        """ Is the active item selection. """
        return self._selection_stack[-1]

    @property
    def view(self) -> ItemView:
        """ Is the active item view. """
        return self._view_stack[-1]

    @property
    def top_view(self) -> ItemView:
        """ Is the top item view. """
        return self._view_stack[0]

    def is_enabled(self, uid: str) -> bool:
        """
        Return true if the item associated with the UID is enabled with
        respect to the active item selection, otherwise return false.
        """
        return self._selection_stack[-1][uid]

    def set_selection(self, selection: ItemSelection) -> None:
        """
        Replace the top of the item selection stack with the selection.
        """
        self._selection_stack[-1] = selection

    def push_selection(self, selection: ItemSelection) -> None:
        """
        Push the item selection to the top of the item selection stack.
        """
        self._selection_stack.append(selection)

    def pop_selection(self) -> None:
        """ Pop the top from the items selection stack. """
        self._selection_stack.pop()

    @contextmanager
    def selection(self, selection: ItemSelection) -> Iterator[None]:
        """ Opens an item selection context. """
        self.push_selection(selection)
        yield
        self.pop_selection()

    def push_view(self, view: ItemView) -> None:
        """ Push the item view to the top of the item view stack. """
        self._view_stack.append(view)

    def pop_view(self) -> None:
        """ Pop the top from the items view stack. """
        self._view_stack.pop()

    @contextmanager
    def view_scope(self, view: ItemView) -> Iterator[None]:
        """ Opens an item view context. """
        self.push_view(view)
        yield
        self.pop_view()

    def _make_item(self, uid: str, data: dict) -> Item:
        if data.get("type", "") == "proxy":
            item: Item = _ProxyItem(self, uid, data)
            self.proxies[uid] = item
        else:
            item = Item(self, uid, data)
            self[uid] = item
        return item

    def add_item(self,
                 uid: str,
                 data: dict,
                 initialize_links: bool = True,
                 set_types: bool = True) -> Item:
        """
        Add an item with the UID and data to the cache and return it.

        The item is not saved to to the persistent cache storage.
        """
        item = self._make_item(uid, data)
        if initialize_links:
            item.init_parents(self)
            item.init_children()
        if set_types:
            self.type_provider.set_type(item)
        return item

    def add_item_from_file(self,
                           uid: str,
                           path: str,
                           initialize_links: bool = True,
                           set_types: bool = True) -> Item:
        """
        Add an item with the UID and the data loaded from the file to the
        cache and return it.
        """
        return self.add_item(uid, load_data(path), initialize_links, set_types)

    def add_items(self,
                  data_by_uid: ItemDataByUID,
                  initialize_links: bool = True,
                  set_types: bool = True) -> None:
        """ Add the data by UID as items to the cache. """
        for uid, data in data_by_uid.items():
            self._make_item(uid, data)
        if initialize_links:
            self.initialize_links(sorted(data_by_uid.keys()))
        if set_types:
            for uid in set(data_by_uid).difference(self.proxies.keys()):
                self.type_provider.set_type(self[uid])

    def load_items(self,
                   path: str | tuple[str, str],
                   initialize_links: bool = True,
                   set_types: bool = True,
                   the_format: str | None = None) -> ItemDataByUID:
        """ Load the items in the path and add them to the cache. """
        if the_format is None:
            the_format = self._format
        if isinstance(path, str):
            uid_prefix = "/"
        else:
            path, uid_prefix = path
        data_by_uid = load_data_by_uid(path, self._cache_directory, uid_prefix,
                                       the_format)
        self.add_items(data_by_uid, initialize_links, set_types)
        return data_by_uid

    def remove_item(self, uid: str) -> None:
        """
        Remove the item associated with the UID with all its links from the
        cache.

        The item is not removed from the persistent cache storage.
        """
        item = self[uid]
        item.clear_links()
        self.type_provider.items_by_type[item.type].remove(item)
        del self[uid]

    def initialize_links(self, uids: Iterable[str]) -> None:
        """ Initialize the links to parents and children. """
        uids = set(uids)
        proxies = set(self.proxies.keys())
        normal_uids = uids.difference(proxies)
        proxy_uids = uids.intersection(proxies)
        for uid in normal_uids:
            self[uid].init_parents(self)
        for uid in normal_uids:
            self[uid].init_children()
        for uid in sorted(proxy_uids):
            self.proxies[uid].init_children()

    def reinitialize_links(self) -> None:
        """ Reinitialize the links to parents and children. """
        # pylint: disable=protected-access
        for item in itertools.chain(self.values(), self.proxies.values()):
            item._links_to_parents = []
            item._links_to_children = []
        self.initialize_links(
            sorted(itertools.chain(self.keys(), self.proxies.keys())))


class EmptyItemCache(ItemCache):
    """ Provides an empty cache of specification items. """

    def __init__(self, type_provider: ItemTypeProvider | None = None) -> None:
        super().__init__(ItemCacheConfig(), type_provider=type_provider)


class JSONItemCache(ItemCache):
    """ Provides a cache of specification items using JSON. """

    def __init__(self,
                 config: ItemCacheConfig,
                 is_item_enabled: IsEnabled = _is_item_enabled,
                 type_provider: ItemTypeProvider | None = None) -> None:
        super().__init__(config, is_item_enabled, type_provider, "json")


class EmptyItem(Item):
    """ Represents an empty item. """

    def __init__(self) -> None:
        super().__init__(EmptyItemCache(), "", {})
