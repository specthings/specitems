# SPDX-License-Identifier: BSD-2-Clause
""" Provides a specification item formatter. """

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

import abc
import subprocess
from typing import Any

import yaml

from .contentmarkdown import format_markdown_text
from .items import Item
from .itemmapper import (from_clang_variables, to_at_variables,
                         to_clang_variables, to_dollar_variables)


class SpecFormatter(abc.ABC):
    """ Provides a method to format values. """

    def __init__(self, clang_format_path: str,
                 clang_format_style: dict[str, str]) -> None:
        super().__init__()
        self.clang_format_path = clang_format_path
        self.clang_format_style = clang_format_style

    @abc.abstractmethod
    def format_value(self, item: Item, path: str, value: Any,
                     fmt: dict) -> None:
        """ Format the value and set the item value according to the path. """

    @abc.abstractmethod
    def save(self, item: Item) -> None:
        """ Save the item if it has a matching format. """


def _format_clang(formatter: SpecFormatter, _item: Item, value: str,
                  fmt: dict) -> str:
    name = fmt["style"]
    try:
        style = formatter.clang_format_style[name]
    except KeyError as err:
        raise ValueError(f"unknown clang-format style '{name}', "
                         "configure it via --clang-format-style") from err
    cmd = [
        formatter.clang_format_path, f"--style={style}",
        "--assume-filename=specitems.c"
    ]
    replacements: dict[str, str] = {}
    value = to_clang_variables(value, replacements)
    result = subprocess.run(cmd,
                            input=value,
                            capture_output=True,
                            encoding="utf-8",
                            check=True)
    return from_clang_variables(result.stdout, replacements)


def _format_myst(_formatter: SpecFormatter, _item: Item, value: str,
                 _fmt: dict) -> str:
    value = to_at_variables(value)
    value = format_markdown_text(value)
    return to_dollar_variables(value)


def _format_sorted(_formatter: SpecFormatter, _item: Item, value: Any,
                   _fmt: dict) -> Any:
    return sorted(value)


def _format_unique(_formatter: SpecFormatter, _item: Item, value: Any,
                   _fmt: dict) -> Any:
    return sorted(set(value))


class _ListOrder(dict):
    pass


def _format_list_order(_formatter: SpecFormatter, item: Item, value: Any,
                       fmt: dict) -> Any:
    # pylint: disable=attribute-defined-outside-init
    value_2 = _ListOrder(value)
    value_2.the_list = item.get_value(  # type: ignore[attr-defined]
        fmt["path"])
    value_2.key = fmt["key"]  # type: ignore[attr-defined]
    return value_2


def _format_list_order_representer(
        representer: yaml.representer.BaseRepresenter, data: Any):
    assert isinstance(representer, yaml.representer.SafeRepresenter)
    order: dict[str, int] = {}
    for index, element in enumerate(data.the_list):
        order[element[data.key]] = index
    if data.keys() != order.keys():
        raise ValueError(
            "the dictionary and order list key sets are not equal: "
            f"{sorted(set(data.keys()).symmetric_difference(order.keys()))}")
    return representer.represent_dict(
        sorted(data.items(), key=lambda x: order[x[0]]))


yaml.add_representer(_ListOrder, _format_list_order_representer)


class _FormatInt(int):
    pass


def _format_int_presenter(representer: yaml.representer.BaseRepresenter,
                          data: Any):
    return representer.represent_scalar('tag:yaml.org,2002:int',
                                        data.fmt.format(data))


yaml.add_representer(_FormatInt, _format_int_presenter)


def _format_int_fmt(value: Any, format_string: str) -> Any:
    # pylint: disable=attribute-defined-outside-init
    value = _FormatInt(value)
    value.fmt = format_string
    return value


def _format_int_string(_formatter: SpecFormatter, _item: Item, value: Any,
                       fmt: dict) -> Any:
    return _format_int_fmt(value, fmt["format"])


def _format_int_attribute(_formatter: SpecFormatter, item: Item, value: Any,
                          fmt: dict) -> Any:
    try:
        format_string = item.get_value(fmt["path"])
    except KeyError:
        format_string = fmt.get("default")
        if format_string is None:
            raise
    return _format_int_fmt(value, format_string)


_YAML_FORMATTER = {
    "myst": _format_myst,
    "clang": _format_clang,
    "int-format-string": _format_int_string,
    "int-format-attribute": _format_int_attribute,
    "list-order": _format_list_order,
    "sorted": _format_sorted,
    "unique": _format_unique,
}


class _ListIndentDumper(yaml.Dumper):
    # pylint: disable=too-many-ancestors

    def increase_indent(self,
                        flow: bool = False,
                        indentless: bool = False) -> None:
        return super().increase_indent(flow, False)


class SpecYAMLFormatter(SpecFormatter):
    """ Provides a method to format values for YAML files. """

    def __init__(self,
                 clang_format_path: str,
                 clang_format_style: dict[str, str],
                 indent_lists: bool = True) -> None:
        super().__init__(clang_format_path, clang_format_style)
        self.indent_lists = indent_lists

    def format_value(self, item: Item, path: str, value: Any,
                     fmt: dict) -> None:
        value = _YAML_FORMATTER[fmt["type"]](self, item, value, fmt)
        item.set_value(path, value)

    def save(self, item: Item) -> None:
        path = item.file
        if path.endswith(".yml"):
            with open(path, "w", encoding="utf-8") as out:
                if self.indent_lists:
                    dumper: type[yaml.Dumper] = _ListIndentDumper
                else:
                    dumper = yaml.Dumper
                out.write(
                    yaml.dump(item.data,
                              Dumper=dumper,
                              default_flow_style=False,
                              allow_unicode=True))
