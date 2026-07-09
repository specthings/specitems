# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the specformatter module. """

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

import dataclasses

import pytest
import specitems
from specitems import EmptyItem, SpecYAMLFormatter


def test_spec_yaml_formatter(tmp_path, monkeypatch):

    @dataclasses.dataclass
    class _Status():
        stdout: str

    def _subprocess_run(cmd, input, capture_output, encoding, check):
        assert cmd == [
            "foo",
            "--style=baz",
            "--assume-filename=specitems.c",
        ]
        assert capture_output
        assert encoding == "utf-8"
        assert check
        if "_Specitems" in input:
            assert input == "void _Specitems(void) {\nclang format input\n}"
            return _Status("""void _Specitems(void)
{
  int a;

  a = b;

  if ( a == 1 ) {
    a = c;
  }

  if ( a == 2 ) {
    a = d;
  }
}
""")
        assert input == "clang format input"
        return _Status("""void f(void)
{
  int a;

  a = b;

  if ( a == 1 ) {
    a = c;
  }

  if ( a == 2 ) {
    a = d;
  }
}

int x;

int g( int a )
{
  return a + a;
}
""")

    monkeypatch.setattr(specitems.specformatter.subprocess, "run",
                        _subprocess_run)

    formatter = SpecYAMLFormatter(clang_format_path="foo",
                                  clang_format_style={"bar": "baz"},
                                  indent_lists=False)
    item = EmptyItem()

    fmt_myst = {"type": "myst"}
    formatter.format_value(item, "/a", "x ${abc:def} y", fmt_myst)
    formatter.format_value(item, "/b", "x ${abc:/def}y", fmt_myst)
    formatter.format_value(item, "/c", "x${/abc:def} y", fmt_myst)
    formatter.format_value(item, "/d", "x${/abc:/def}y", fmt_myst)

    fmt_int_string = {"type": "int-format-string", "format": "{:#04x}"}
    formatter.format_value(item, "/e", 1, fmt_int_string)

    fmt_int_attribute = {"type": "int-format-attribute", "path": "/f"}
    item["f"] = "{:#05x}"
    formatter.format_value(item, "/g", 2, fmt_int_attribute)

    fmt_int_default = {
        "type": "int-format-attribute",
        "path": "/nix",
    }
    with pytest.raises(KeyError):
        formatter.format_value(item, "/h", 3, fmt_int_default)

    fmt_int_default["default"] = "{:#06x}"
    formatter.format_value(item, "/h", 3, fmt_int_default)

    fmt_clang_format = {"type": "clang", "style": "nix", "scope": "file"}
    with pytest.raises(ValueError):
        formatter.format_value(item, "/i", "clang format input",
                               fmt_clang_format)
    fmt_clang_format["style"] = "bar"
    formatter.format_value(item, "/i", "clang format input", fmt_clang_format)
    fmt_clang_format["scope"] = "function"
    formatter.format_value(item, "/j", "clang format input", fmt_clang_format)

    fmt_list_order = {"type": "list-order", "path": "/k", "key": "l"}
    item["k"] = [{"l": "b"}]
    formatter.format_value(item, "/l", {"a": 1, "b": 2}, fmt_list_order)

    fmt_sorted = {"type": "sorted"}
    formatter.format_value(item, "/m", [2, 1], fmt_sorted)

    fmt_unique = {"type": "unique"}
    formatter.format_value(item, "/n", [4, 3, 4, 3, 3], fmt_unique)

    assert item.data == {
        "a":
        "x ${abc:def} y\n",
        "b":
        "x ${abc:/def}y\n",
        "c":
        "x${/abc:def} y\n",
        "d":
        "x${/abc:/def}y\n",
        "e":
        1,
        "f":
        "{:#05x}",
        "g":
        2,
        "h":
        3,
        "i":
        "void f(void)\n"
        "{\n"
        "  int a;\n"
        "\n"
        "  a = b;\n"
        "\n"
        "  if ( a == 1 ) {\n"
        "    a = c;\n"
        "  }\n"
        "\n"
        "  if ( a == 2 ) {\n"
        "    a = d;\n"
        "  }\n"
        "}\n"
        "\n"
        "int x;\n"
        "\n"
        "int g( int a )\n"
        "{\n"
        "  return a + a;\n"
        "}\n",
        "j":
        "int a;\n"
        "\n"
        "a = b;\n"
        "\n"
        "if ( a == 1 ) {\n"
        "  a = c;\n"
        "}\n"
        "\n"
        "if ( a == 2 ) {\n"
        "  a = d;\n"
        "}\n",
        "k": [{
            "l": "b"
        }],
        "l": {
            "a": 1,
            "b": 2
        },
        "m": [1, 2],
        "n": [3, 4],
    }

    item.file = "something.txt"
    formatter.save(item)

    file_path = tmp_path / "item.yml"
    item.file = str(file_path)

    with pytest.raises(ValueError):
        formatter.save(item)
    item["k"].append({"l": "a"})

    formatter.save(item)
    assert file_path.read_text(encoding="utf-8") == """a: |
  x ${abc:def} y
b: |
  x ${abc:/def}y
c: |
  x${/abc:def} y
d: |
  x${/abc:/def}y
e: 0x01
f: '{:#05x}'
g: 0x002
h: 0x0003
i: |
  void f(void)
  {
    int a;

    a = b;

    if ( a == 1 ) {
      a = c;
    }

    if ( a == 2 ) {
      a = d;
    }
  }

  int x;

  int g( int a )
  {
    return a + a;
  }
j: |
  int a;

  a = b;

  if ( a == 1 ) {
    a = c;
  }

  if ( a == 2 ) {
    a = d;
  }
k:
- l: b
- l: a
l:
  b: 2
  a: 1
m:
- 1
- 2
n:
- 3
- 4
"""

    file_path_2 = tmp_path / "item_2.yml"
    item.file = str(file_path_2)
    formatter.indent_lists = True
    formatter.save(item)
    assert file_path_2.read_text(encoding="utf-8") == """a: |
  x ${abc:def} y
b: |
  x ${abc:/def}y
c: |
  x${/abc:def} y
d: |
  x${/abc:/def}y
e: 0x01
f: '{:#05x}'
g: 0x002
h: 0x0003
i: |
  void f(void)
  {
    int a;

    a = b;

    if ( a == 1 ) {
      a = c;
    }

    if ( a == 2 ) {
      a = d;
    }
  }

  int x;

  int g( int a )
  {
    return a + a;
  }
j: |
  int a;

  a = b;

  if ( a == 1 ) {
    a = c;
  }

  if ( a == 2 ) {
    a = d;
  }
k:
  - l: b
  - l: a
l:
  b: 2
  a: 1
m:
  - 1
  - 2
n:
  - 3
  - 4
"""
