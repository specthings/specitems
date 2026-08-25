# SPDX-License-Identifier: BSD-2-Clause
"""
Print the specification item type-refinement tree.
"""

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

import argparse
import importlib.metadata
import os
import re
import shutil
import sys
import textwrap
from typing import Iterable, Iterator, NamedTuple, Optional

from .items import Item, ItemCache, ItemCacheConfig, ItemDataByUID, \
    ItemTypeProvider, pickle_load_data_by_uid

# names/types below are meant to speak for themselves; no docstring needed
# pylint: disable=missing-class-docstring,missing-function-docstring

_TYPE_PROVIDER_PLUGIN_GROUP = "specitems_type_provider.plugins"
_ROOT_UID = "/spec/root"
_UID_PREFIX = "/spec/"
_FALLBACK_WIDTH = 100


def _effective_width() -> int:
    return shutil.get_terminal_size(fallback=(_FALLBACK_WIDTH, 24)).columns


def _defining_file(uid: str) -> str:
    relative = uid[len(_UID_PREFIX):] if uid.startswith(_UID_PREFIX) else uid
    return relative + ".yml"


class _PassthroughTypeProvider(ItemTypeProvider):
    """ Feeds pre-merged type items into an ItemCache without classifying
    each item's own semantic type -- classification is not needed to walk
    spec-refinement/spec-member links. """

    def __init__(self, data_by_uid: ItemDataByUID) -> None:
        super().__init__(data_by_uid, None)
        self.data_by_uid = data_by_uid

    def set_type(self, _item: Item) -> None:
        pass


def _package_type_data() -> Iterator[tuple[str, ItemDataByUID]]:
    """ Yield (package, its type items) for specitems and every package
    registered as a specitems_type_provider.plugins entry point. """
    yield "specitems", pickle_load_data_by_uid(
        os.path.join(os.path.dirname(__file__), "spec.pickle"))
    for entry_point in importlib.metadata.entry_points(
            group=_TYPE_PROVIDER_PLUGIN_GROUP):
        yield (entry_point.module.split(".",
                                        maxsplit=1)[0], entry_point.load()())


def load_type_items() -> tuple[ItemDataByUID, dict[str, str]]:
    data_by_uid: ItemDataByUID = {}
    package_by_uid: dict[str, str] = {}
    for package, package_data in _package_type_data():
        for uid, data in package_data.items():
            existing_package = package_by_uid.get(uid)
            if existing_package is not None and existing_package != package:
                same_content = data_by_uid[uid] == data
                print(
                    f"warning: '{package}' redefines the type from "
                    f"'{_defining_file(uid)}' already provided by "
                    f"'{existing_package}'"
                    f"{'' if same_content else ' (with different content)'}"
                    f"; using the '{package}' definition",
                    file=sys.stderr)
            data_by_uid[uid] = data
            package_by_uid[uid] = package
    return data_by_uid, package_by_uid


_REQUIREMENT_NAME = re.compile(r"^[A-Za-z0-9_.-]+")


def packages_up_to(package_name: str,
                   known_packages: Iterable[str]) -> set[str]:
    """ `package_name` plus every `known_packages` member it (transitively)
    depends on. """
    known = set(known_packages)
    closure = {package_name}
    pending = [package_name]
    while pending:
        current = pending.pop()
        for requirement in importlib.metadata.requires(current) or []:
            match = _REQUIREMENT_NAME.match(requirement)
            if match is None:
                continue
            dependency = match.group(0)
            if dependency in known and dependency not in closure:
                closure.add(dependency)
                pending.append(dependency)
    return closure


def _label_parts(item: Item, package_by_uid: dict[str, str]) -> list[str]:
    """ `item`'s own display parts: the file it is defined in and its
    package, the value kinds (bool/dict/list/none/str/...) it accepts,
    and its brief name. """
    kinds = "|".join(sorted(item["spec-info"]))
    return [
        _defining_file(item.uid), f"({package_by_uid[item.uid]})",
        f"{{{kinds}}}", item["spec-name"]
    ]


def _wrap_bracket(first_prefix: str, continuation_prefix: str, edge_key: str,
                  edge_values: list[str], width: int) -> list[str]:
    """ Render ``[key=v1|v2|...]`` packed onto as few lines as fit in
    `width`, breaking only between values, never inside one. """
    opening = f"[{edge_key}=" if edge_key else "["
    tokens = [opening + edge_values[0]
              ] + [f"|{value}" for value in edge_values[1:]]
    lines: list[str] = []
    prefix = first_prefix
    current = prefix
    last_index = len(tokens) - 1
    for index, token in enumerate(tokens):
        bracket_width = 1 if index == last_index else 0
        candidate = current + token
        if current != prefix and len(candidate) + bracket_width > width:
            lines.append(current)
            prefix = continuation_prefix
            current = prefix + token
        else:
            current = candidate
    lines.append(current + "]")
    return lines


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _print_entry(prefix: str, connector: str, continuation_prefix: str,
                 edge_key: str, edge_values: list[str], label_parts: list[str],
                 width: int) -> None:
    """ Print one entry: ``prefix connector [key=value] file.yml (package)
    {kinds} name``, splitting it across lines only when it doesn't fit
    `width`. """
    edge_text = ""
    if edge_values:
        edge_text = (f"[{edge_key}={'|'.join(edge_values)}]"
                     if edge_key else f"[{'|'.join(edge_values)}]")

    components = ([edge_text] if edge_text else []) + label_parts
    full_line = f"{prefix}{connector}" + " ".join(components)
    if len(full_line) <= width:
        print(full_line)
        return

    line_prefix = prefix + connector
    if edge_text:
        for line in _wrap_bracket(line_prefix, continuation_prefix, edge_key,
                                  edge_values, width):
            print(line)
        line_prefix = continuation_prefix
    for part in label_parts:
        line = line_prefix + part
        if len(line) > width:
            # avoid splitting an overlong uid/name mid-word
            wrapped_lines = textwrap.wrap(
                part,
                width=width,
                initial_indent=line_prefix,
                subsequent_indent=continuation_prefix,
                break_on_hyphens=False,
                break_long_words=False)
            for wrapped in wrapped_lines or [line]:
                print(wrapped)
        else:
            print(line)
        line_prefix = continuation_prefix


class _Node(NamedTuple):
    """ An item plus the spec-refinement edge it was reached by (empty for
    a tree/forest root, which by definition has no such edge). """
    item: Item
    key: str = ""
    values: tuple[str, ...] = ()


class _TreeContext(NamedTuple):
    package_by_uid: dict[str, str]
    allowed_uids: Optional[set[str]]
    width: int
    visited: set[str]


def _hierarchy_children(ctx: _TreeContext, item: Item) -> list[_Node]:
    # a child may refine its parent through more than one spec-refinement
    # link (e.g. pkg-sphinx-types refines pkg-sphinx-document once per
    # document-type value it stands in for); collect all of a child's
    # values into one _Node so it is listed only once
    by_uid: dict[str, tuple[Item, str, list[str]]] = {}
    for link in item.links_to_children("spec-refinement"):
        if ctx.allowed_uids is not None and link.uid not in ctx.allowed_uids:
            continue
        _, key, values = by_uid.setdefault(link.uid,
                                           (link.item, link["spec-key"], []))
        values.append(link["spec-value"])
    return [
        _Node(child, key, tuple(sorted(values)))
        for child, key, values in sorted(by_uid.values(),
                                         key=lambda entry: entry[0].uid)
    ]


# pylint: disable-next=too-many-arguments,too-many-positional-arguments
def _print_tree(ctx: _TreeContext,
                node: _Node,
                prefix: str = "",
                is_last: bool = True,
                is_root: bool = True,
                root_connector: str = "") -> None:
    ctx.visited.add(node.item.uid)
    if is_root:
        connector = root_connector
        child_prefix = prefix + " " * len(root_connector)
    else:
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")
    _print_entry(prefix, connector, child_prefix, node.key, list(node.values),
                 _label_parts(node.item, ctx.package_by_uid), ctx.width)
    children = _hierarchy_children(ctx, node.item)
    for index, child in enumerate(children):
        _print_tree(ctx, child, child_prefix, index == len(children) - 1,
                    False)


def _refines_nothing(item: Item) -> bool:
    return next(item.parents("spec-refinement"), None) is None


def _print_members(ctx: _TreeContext, item_cache: ItemCache) -> None:
    """ Print every loaded type not reached while walking the refinement
    tree from root as a forest of its own subtrees. """
    uids = item_cache.keys() if ctx.allowed_uids is None else ctx.allowed_uids
    unvisited = [item_cache[uid] for uid in uids if uid not in ctx.visited]
    if not unvisited:
        return
    print()
    print("Types not reachable from the root type via spec-refinement:")
    roots = sorted((item for item in unvisited if _refines_nothing(item)),
                   key=lambda item: item.uid)
    for root_item in roots:
        _print_tree(ctx, _Node(root_item), root_connector="- ")
    # anything still unvisited refines a type excluded by --package, so
    # there is no root to nest it under here; show it anyway, flat
    for uid in sorted(uid for uid in uids if uid not in ctx.visited):
        _print_entry("", "- ", "  ", "", [],
                     _label_parts(item_cache[uid], ctx.package_by_uid),
                     ctx.width)


def _ancestor_chain(item: Item) -> list[_Node]:
    nodes = [_Node(item)]
    current = item
    while True:
        try:
            parent_link = current.parent_link("spec-refinement")
        except IndexError:
            break
        same_parent = [
            link for link in current.links_to_parents("spec-refinement")
            if link.uid == parent_link.uid
        ]
        key = same_parent[0]["spec-key"]
        values = tuple(sorted(link["spec-value"] for link in same_parent))
        nodes[-1] = nodes[-1]._replace(key=key, values=values)
        nodes.append(_Node(parent_link.item))
        current = parent_link.item
    nodes.reverse()
    return nodes


def _print_ancestors(package_by_uid: dict[str, str], item: Item,
                     width: int) -> None:
    for depth, node in enumerate(_ancestor_chain(item)):
        prefix = "    " * depth
        connector = "" if depth == 0 else "└── "
        continuation_prefix = "    " * (depth + 1)
        _print_entry(prefix, connector, continuation_prefix, node.key,
                     list(node.values), _label_parts(node.item,
                                                     package_by_uid), width)


def _find(pool: dict[str, Item], name: str) -> Item:
    """ Find a type item by UID, short UID, defining file name (e.g.
    "build.yml"), or `spec-type` slug. """
    if name.endswith(".yml"):
        name = name[:-len(".yml")]
    if name in pool:
        return pool[name]
    prefixed = _UID_PREFIX + name
    if not name.startswith("/") and prefixed in pool:
        return pool[prefixed]
    candidates = [item for item in pool.values() if item["spec-type"] == name]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise SystemExit(f"no type named or UID'd '{name}' found")
    raise SystemExit(f"ambiguous type name '{name}': "
                     f"{', '.join(sorted(item.uid for item in candidates))}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=clitypeview.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--ancestors",
        metavar="TYPE",
        default=None,
        help="print only the ancestor chain from the root down to TYPE, "
        "not its subtree")
    parser.add_argument(
        "--package",
        metavar="PACKAGE",
        default=None,
        help="only show types up to this package: the package itself "
        "plus every package it depends on -- e.g. --package specware "
        "shows specitems and specware, but not specmake")
    return parser.parse_args(argv[1:])


def clitypeview(argv: list[str] = sys.argv) -> Optional[int]:
    """ Print the specification item type-refinement tree. """
    args = _parse_args(argv)

    data_by_uid, package_by_uid = load_type_items()
    item_cache = ItemCache(ItemCacheConfig(),
                           type_provider=_PassthroughTypeProvider(data_by_uid))

    allowed_uids: Optional[set[str]] = None
    if args.package:
        known_packages = set(package_by_uid.values())
        if args.package not in known_packages:
            print(
                f"unknown package '{args.package}'; discovered packages "
                f"are: {', '.join(sorted(known_packages))}",
                file=sys.stderr)
            return 1
        allowed_packages = packages_up_to(args.package, known_packages)
        allowed_uids = {
            uid
            for uid, package in package_by_uid.items()
            if package in allowed_packages
        }

    width = _effective_width()
    pool = (item_cache if allowed_uids is None else {
        uid: item_cache[uid]
        for uid in allowed_uids
    })

    if args.ancestors:
        _print_ancestors(package_by_uid, _find(pool, args.ancestors), width)
        return None

    if _ROOT_UID not in item_cache:
        print(
            f"the root type '{_ROOT_UID}' was not found; is specitems "
            "installed correctly?",
            file=sys.stderr)
        return 1

    ctx = _TreeContext(package_by_uid, allowed_uids, width, set())
    _print_tree(ctx, _Node(item_cache[_ROOT_UID]))
    _print_members(ctx, item_cache)
    return None
