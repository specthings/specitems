# SPDX-License-Identifier: BSD-2-Clause
""" Provides mappings to get context-sensitive item values. """

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
import contextlib
import copy
import dataclasses
import os
import re
import string
from typing import Any, Callable, Iterator, Optional

from .items import Item, ItemType

ItemGetValue = Callable[["ItemGetValueContext"], Any]
ItemGetValueMap = dict[str, tuple[ItemGetValue, Any]]


class _ItemTemplate(string.Template):
    """ String template for item mapper identifiers. """
    idpattern = "(?:[a-zA-Z0-9._/-]+|\\*):[\\[\\]a-zA-Z0-9._/-]+(?::[^${}]*)?"


class _ItemMapperContext(dict):
    """
    Provides a context to map identifiers to items and attribute values.
    """

    def __init__(self, mapper: "ItemMapper", item: Optional[Item],
                 prefix: str) -> None:
        super().__init__()
        self._mapper = mapper
        self._item = item
        self._prefix = prefix

    def __getitem__(self, identifier: str) -> Any:
        return self._mapper.map(identifier, self._item, self._prefix)[2]


_SINGLE_SUBSTITUTION = re.compile(f"^\\${{{_ItemTemplate.idpattern}}}$")


class _GetValueDictionary(dict):

    def __init__(self, get_value: ItemGetValue) -> None:
        super().__init__()
        self._get_value = get_value

    def get(self, _key, _default):
        return (self._get_value, {})


def unpack_arg(arg: str) -> str:
    """ Unpack the argument by undoing character escapes. """
    # pylint: disable=too-many-branches
    arg_2: list[str] = []
    unpack = False
    for i in arg:
        if unpack:
            unpack = False
            match i:
                case "0":
                    arg_2.append("\0")
                case "a":
                    arg_2.append("\a")
                case "b":
                    arg_2.append("\b")
                case "c":
                    arg_2.append(",")
                case "f":
                    arg_2.append("\f")
                case "n":
                    arg_2.append("\n")
                case "r":
                    arg_2.append("\r")
                case "s":
                    arg_2.append(" ")
                case "t":
                    arg_2.append("\t")
                case "v":
                    arg_2.append("\v")
                case "%":
                    arg_2.append("%")
                case "(":
                    arg_2.append("(")
                case ")":
                    arg_2.append(")")
                case "\\":
                    arg_2.append("\\")
                case _:
                    arg_2.append(i)
        else:
            match i:
                case "%":
                    arg_2.append("$")
                case "(":
                    arg_2.append("{")
                case ")":
                    arg_2.append("}")
                case "\\":
                    unpack = True
                case _:
                    arg_2.append(i)
    return "".join(arg_2)


def unpack_args(
        optional_args: Optional[str],
        substitute: Callable[[str], str]) -> tuple[list[str], dict[str, str]]:
    """
    Unpack the optional arguments to positional arguments and keyword
    arguments.

    Substitute the positional arguments and the keyword argument values.
    """
    args: list[str] = []
    kwargs: dict[str, str] = {}
    if optional_args:
        for kv in optional_args.split(","):
            key, sep, value = kv.partition("=")
            if sep:
                kwargs[key] = substitute(unpack_arg(value))
            else:
                args.append(substitute(unpack_arg(key)))
    return args, kwargs


def _identity(value: str) -> str:
    return value


@dataclasses.dataclass
class ItemGetValueContext:
    """ Provides a context to get an item value. """

    # pylint: disable=too-many-instance-attributes

    item: Item
    remaining_path: str
    args: Optional[str]
    value: Any
    mapper: "ItemMapper"
    get_value_map: ItemGetValueMap
    path: str = ""
    key_index: str = ""
    key: str = ""
    index: int = -1

    def arg(self, name: str, value: Optional[str] = None) -> str:
        """ Get the argument value by name. """
        _, kwargs = self.unpack_args_dict()
        if value is None:
            return kwargs[name]
        return kwargs.get(name, value)

    def unpack_args_list(self) -> list[str]:
        """ Unpack the context arguments to a list. """
        if self.args is None:
            return []
        return [unpack_arg(arg) for arg in self.args.split(",")]

    def unpack_args_dict(
        self,
        substitute: Callable[[str], str] = _identity
    ) -> tuple[list[str], dict[str, str]]:
        """
        Unpack the context arguments to positional arguments and keyword
        arguments.
        """
        return unpack_args(self.args, substitute)

    def substitute(self, value: Any) -> Any:
        """ Substitute the value using the mapper of the context. """
        return self.mapper.substitute_data(value, self.item, self.path)

    def transform(self, value: Any) -> Any:
        """
        Transform the value using the transformer specified by the context
        arguments.

        If the context arguments are not present, then return the value.
        """
        if self.args is None:
            return value

        def _substitute(text: str) -> str:
            return self.mapper.substitute(text, self.item, self.path)

        return self.mapper.transform(value, self.args, _substitute)

    def substitute_and_transform(self, value: Any) -> Any:
        """
        Substitute the value and transform the substituted value using the
        transformer specified by the context arguments.

        If the context arguments are not present, then return the substituted
        value.
        """
        return self.transform(self.substitute(value))

    def reset(self, item: Item, key_path: str) -> dict:
        """
        Reset the context to use the item and key path.

        Returns the data of the item.
        """
        self.item = item
        self.remaining_path = key_path
        self.get_value_map = self.mapper.get_value_map(item)
        self.path = ""
        self.key_index = ""
        return item.data


def get_value_default(ctx: ItemGetValueContext) -> Any:
    """ Get the value by default. """
    return ctx.mapper.get_value_default(ctx)


def _normalize_key_path(key_path: str, prefix: str) -> str:
    """ Normalize the key path with an optional prefix path. """
    if not os.path.isabs(key_path):
        key_path = os.path.join(prefix, key_path)
    return os.path.normpath(key_path)


class ItemMapper(abc.ABC):
    """ Maps identifiers to items and attribute values. """

    _copyrights_by_license: dict[str, set[str]] = {}

    def __init__(self, item: Item) -> None:
        self.item = item
        self._default_get_value_map: ItemGetValueMap = {}
        self._get_value_map: dict[str, ItemGetValueMap] = {}
        self._value_providers: list["ItemValueProvider"] = []
        self._transformers: dict[str, Callable] = {}

    @property
    def copyrights_by_license(self) -> dict[str, set[str]]:
        """ The item copyrights by license. """
        return ItemMapper._copyrights_by_license

    def get_value_default(self, ctx: ItemGetValueContext) -> Any:
        """ Get the value by default. """
        value = ctx.value[ctx.key]
        if ctx.index >= 0:
            value = value[ctx.index]
        if not ctx.remaining_path:
            value = self.substitute_data(value, ctx.item, ctx.path)
            if ctx.args is not None:

                def _substitute(text: str) -> str:
                    return self.substitute(text, ctx.item, ctx.path)

                value = self.transform(value, ctx.args, _substitute)
        return value

    def _add_get_value_map_for_subtypes(
            self, spec_type: ItemType, type_path: str, path_key: str,
            new_get_value_map: tuple[ItemGetValue, dict]) -> None:
        if spec_type.refinements:
            for key, refinement in spec_type.refinements.items():
                self._add_get_value_map_for_subtypes(refinement,
                                                     f"{type_path}/{key}",
                                                     path_key,
                                                     new_get_value_map)
        else:
            keys = path_key.strip("/").split("/")
            get_value_map = self._get_value_map.setdefault(
                type_path, copy.copy(self._default_get_value_map))
            for key in keys[:-1]:
                _, get_value_map = get_value_map.setdefault(
                    key, (self.get_value_default, {}))
            get_value_map[keys[-1]] = new_get_value_map

    def _add_get_value_map(
            self, type_path_key: str, new_get_value_map: tuple[ItemGetValue,
                                                               dict]) -> None:
        type_name, path_key = type_path_key.split(":")
        spec_type = self.item.cache.type_provider.root_type
        for name in type_name.split("/"):
            spec_type = spec_type.refinements[name]
        self._add_get_value_map_for_subtypes(spec_type, type_name, path_key,
                                             new_get_value_map)

    def add_default_get_value(self, key: str, get_value: ItemGetValue) -> None:
        """
        Associate the get value method with the key in the default get value
        map.

        The default get value map is used to initialize a type-specific get
        value map.
        """
        self._default_get_value_map[key] = (get_value, {})
        for get_value_map in self._get_value_map.values():
            assert key not in get_value_map
            get_value_map[key] = (get_value, {})

    def add_get_value(self, type_path_key: str,
                      get_value: ItemGetValue) -> None:
        """
        Associate the get value method with the type/key path.
        """
        self._add_get_value_map(type_path_key, (get_value, {}))

    def add_get_value_dictionary(self, type_path_key: str,
                                 get_value: ItemGetValue) -> None:
        """
        Associate the get value dictionary with the type/key path.
        """
        self._add_get_value_map(
            type_path_key,
            (self.get_value_default, _GetValueDictionary(get_value)))

    def add_value_transformer(self, name: str, transformer: Callable) -> None:
        """
        Associate the name with the value transformer.

        The transformer is used to transform a mapped value.  The mapped value
        is passed as the first argument to the transformer.
        """
        self._transformers[name] = transformer

    def transform(self, value: Any, name_and_args: str,
                  substitute: Callable[[str], str]) -> Any:
        """
        Transform the value using the transformer specified by the name and
        optional arguments.

        The value is passed as the first argument to the transformer.

        The name and arguments string parameter specifies the name of the
        transformer and optional additional positional and keyword arguments.
        The transformer name is the start of the string up to the first space
        character or the end of the string.  Arguments following the space
        character are unpacked and passed to the transformer.
        """
        name, _, args_string = name_and_args.partition(" ")
        args, kwargs = unpack_args(args_string, substitute)
        return self._transformers[name](value, *args, **kwargs)

    @contextlib.contextmanager
    def scope(self, item: Item) -> Iterator[None]:
        """ Opens an item scope context. """
        previous = self.item
        self.item = item
        yield
        self.item = previous

    def get_value_map(self, item: Item) -> ItemGetValueMap:
        """ Return the get value map for the item. """
        return self._get_value_map.get(item.type, self._default_get_value_map)

    def _get_by_normalized_key_path(
            self, item: Item, normalized_key_path: str,
            args: Optional[str]) -> ItemGetValueContext:
        """
        Get the attribute value associated with the normalized key path.
        """
        ctx = ItemGetValueContext(item, normalized_key_path.strip("/"), args,
                                  item.data, self, self.get_value_map(item))
        while ctx.remaining_path:
            key_end = ctx.remaining_path.find("/")
            if key_end >= 0:
                key_index = ctx.remaining_path[:key_end]
                ctx.remaining_path = ctx.remaining_path[key_end + 1:]
            else:
                key_index = ctx.remaining_path
                ctx.remaining_path = ""
            ctx.path = f"{ctx.path}/{ctx.key_index}".replace("//", "/")
            ctx.key_index = key_index
            parts = key_index.split("[")
            ctx.key = parts[0]
            try:
                ctx.index = int(parts[1].split("]")[0])
            except IndexError:
                ctx.index = -1
            get_value, ctx.get_value_map = ctx.get_value_map.get(
                parts[0], (self.get_value_default, {}))
            ctx.value = get_value(ctx)
        self.copyrights_by_license.setdefault(item["SPDX-License-Identifier"],
                                              set()).update(item["copyrights"])
        return ctx

    def map(self,
            identifier: str,
            item: Optional[Item] = None,
            prefix: str = "") -> tuple[Item, str, Any]:
        """
        Map the identifier with item and prefix to the associated item, key
        path, and attribute value.
        """
        colon = identifier.find(":")
        uid = identifier[:colon]
        more = identifier[colon + 1:]
        colon = more.find(":")
        if colon < 0:
            key_path = more
            args = None
        else:
            key_path = more[:colon]
            args = more[colon + 1:]
        if uid == "*":
            item = self.item
            prefix = ""
        else:
            if item is None:
                item = self.item
            if uid != ".":
                prefix = ""
                try:
                    item = item.map(uid)
                except KeyError as err:
                    msg = (f"item '{uid}' relative to {item.spec} "
                           f"specified by '{identifier}' does not exist")
                    raise ValueError(msg) from err
        key_path = _normalize_key_path(key_path, prefix)
        try:
            ctx = self._get_by_normalized_key_path(item, key_path, args)
        except Exception as err:
            msg = (f"cannot get value for '{key_path}' of {item.spec} "
                   f"specified by '{identifier}'")
            raise ValueError(msg) from err
        return ctx.item, f"{ctx.path}/{ctx.key_index}".replace("//",
                                                               "/"), ctx.value

    def __getitem__(self, identifier: str) -> Any:
        return self.map(identifier)[2]

    def substitute(self,
                   text: Optional[str],
                   item: Optional[Item] = None,
                   prefix: str = "") -> str:
        """
        Perform a variable substitution using the item mapper with the item
        and prefix.
        """
        if not text:
            return ""
        try:
            context = _ItemMapperContext(self, item, prefix)
            return _ItemTemplate(text).substitute(context)
        except Exception as err:
            spec = self.item.spec if item is None else item.spec
            enumerated = "\n".join(f"{i + 1:>5}: {line}"
                                   for i, line in enumerate(text.splitlines()))
            msg = (f"substitution for {spec} using prefix '{prefix}' "
                   f"failed for text:\n{enumerated}")
            raise ValueError(msg) from err

    def substitute_data(self,
                        data: Any,
                        item: Optional[Item] = None,
                        prefix: str = "") -> Any:
        """
        Perform a recursive substitution of the data elements using the item
        mapper with the item.
        """
        if isinstance(data, str):
            return self.substitute(data, item, prefix)
        if isinstance(data, list):
            new_list: list[Any] = []
            for index, element in enumerate(data):
                prefix_2 = f"{prefix}[{index}]"
                if isinstance(element, str):
                    match = _SINGLE_SUBSTITUTION.search(element)
                    if match:
                        new_element = self.map(element[2:-1], item,
                                               prefix_2)[2]
                        if isinstance(new_element, list):
                            new_list.extend(new_element)
                        else:
                            new_list.append(new_element)
                    else:
                        new_list.append(
                            self.substitute(element, item, prefix_2))
                else:
                    new_list.append(
                        self.substitute_data(element, item, prefix_2))
            return new_list
        if isinstance(data, dict):
            new_dict: dict[Any, Any] = {}
            for key, value in data.items():
                new_dict[self.substitute(key, item)] = self.substitute_data(
                    value, item, os.path.join(prefix, key))
            return new_dict
        return data

    def add_value_provider(self, provider: "ItemValueProvider") -> None:
        """ Add the value provider to the mapper. """
        self._value_providers.append(provider)

    def reset(self) -> None:
        """ Reset the mapper state and the registered value providers.  """
        for provider in self._value_providers:
            provider.reset()


class ItemValueProvider:
    """ Provides values for the item mapper. """

    # pylint: disable=too-few-public-methods

    def __init__(self, mapper: ItemMapper) -> None:
        self.mapper = mapper
        mapper.add_value_provider(self)

    def reset(self) -> None:
        """ Reset the value provider state. """
