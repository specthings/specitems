# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the content module. """

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

from specitems.content import (Content, get_value_plural, make_lines,
                               to_camel_case, list_terms)
from specitems.items import EmptyItemCache
from specitems.itemmapper import ItemGetValueContext, ItemMapper


def test_to_camel_case():
    assert to_camel_case("/x") == "X"
    assert to_camel_case("/ab cd?ef+") == "AbCdEfX"


def test_list_terms():
    assert list_terms([]) == ""
    assert list_terms(["a"]) == "a"
    assert list_terms(["a", "b"]) == "a and b"
    assert list_terms(["a", "b", "c"], conjunction="or") == "a, b, or c"


def test_tab():
    content = Content("BSD-2-Clause")
    assert content.tab == "  "


def test_append():
    content = Content("BSD-2-Clause")
    content.append("")
    assert str(content) == """
"""
    assert content.join() == ""
    content.append(["a", "b"])
    assert str(content) == """
a
b
"""
    assert content.join() == """
a
b"""
    with content.indent(levels=2):
        content.append(["c", "d"])
        assert str(content) == """
a
b
    c
    d
"""
    with content.indent(levels=0):
        content.append(["e", "f"])
        assert str(content) == """
a
b
    c
    d
e
f
"""


def test_prepend():
    content = Content("BSD-2-Clause")
    content.prepend(None)
    content.prepend("")
    assert str(content) == """
"""
    content.prepend(["a", "b"])
    assert str(content) == """a
b

"""
    with content.indent():
        content.prepend(["c", "d"])
        assert str(content) == """c
d
a
b

"""


def test_add():
    content = Content("BSD-2-Clause")
    assert not content
    content.add("")
    assert not content
    assert str(content) == ""
    content.add([""])
    assert not content
    assert str(content) == ""
    content.add("a")
    assert content
    assert str(content) == """a
"""
    content.add(["b", "c"])
    assert str(content) == """a

b
c
"""
    content = Content("BSD-2-Clause")
    content.add("a")
    assert str(content) == """a
"""
    content.add_blank_line()
    assert str(content) == """a

"""
    content.add("b")
    assert str(content) == """a

b
"""
    content = Content("BSD-2-Clause")
    content.add("a")
    assert str(content) == """a
"""
    content.ensure_blank_line()
    assert str(content) == """a

"""
    content.add("b")
    assert str(content) == """a

b
"""


def test_wrap():
    content = Content("BSD-2-Clause")
    assert not content.gap
    content.wrap("")
    assert not content.gap
    assert str(content) == ""
    content.wrap("a")
    assert content.gap
    assert str(content) == """a
"""
    content.wrap(["b", "c"])
    assert str(content) == """a

b c
"""
    content.wrap(content)
    assert str(content) == """a

b c

a

b c
"""
    content = Content("BSD-2-Clause")
    content.wrap("\n")
    assert str(content) == ""
    content = Content("BSD-2-Clause")
    content.wrap("x", initial_indent="i")
    assert str(content) == """ix
"""
    content = Content("BSD-2-Clause")
    content.wrap(["a", "", "  b"])
    assert str(content) == """a

  b
"""
    content = Content("BSD-2-Clause")
    content.wrap("one two three four five six seven eight nine ten one two "
                 "three four five six seven eight nine ten")
    assert str(
        content
    ) == """one two three four five six seven eight nine ten one two three four five six
seven eight nine ten
"""
    content = Content("BSD-2-Clause")
    content.text_width = 100
    content.wrap("one two three four five six seven eight nine ten one two "
                 "three four five six seven eight nine ten")
    assert str(
        content
    ) == """one two three four five six seven eight nine ten one two three four five six seven eight nine ten
"""
    content = Content("BSD-2-Clause")
    content.wrap([
        "a", "", "* b",
        "cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff",
        "ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii",
        "jjjjjjjjjjjjjjjjjjj"
    ])
    assert str(content) == """a

* b cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff
  ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii
  jjjjjjjjjjjjjjjjjjj
"""
    content = Content("BSD-2-Clause")
    content.wrap([
        "a", "", "- b",
        "cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff",
        "ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii",
        "jjjjjjjjjjjjjjjjjjj"
    ])
    assert str(content) == """a

- b cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff
  ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii
  jjjjjjjjjjjjjjjjjjj
"""
    content = Content("BSD-2-Clause")
    content.wrap([
        "a", "", "- b",
        "cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff",
        "ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii",
        "jjjjjjjjjjjjjjjjjjj"
    ])
    assert str(content) == """a

- b cccccccccccc ddddddddddddddddd eeeeeeeeeeeeeeeeeeee ffffffffffffffff
  ggggggggggggggggg hhhhhhhhhhhhhhhhhhhhhhhhh iiiiiiiiiiiiiiii
  jjjjjjjjjjjjjjjjjjj
"""
    content = Content("BSD-2-Clause")
    content.wrap(
        """- one two three four five six seven eight nine ten one two three four five six seven eight nine ten

  - one two three four five six seven eight nine ten one two three four five six seven eight nine ten

    * one two three four five six seven eight nine ten one two three four five six seven eight nine ten

  1. one two three four five six seven eight nine ten one two three four five six seven eight nine ten"""
    )
    assert str(
        content
    ) == """- one two three four five six seven eight nine ten one two three four five six
  seven eight nine ten

  - one two three four five six seven eight nine ten one two three four five
    six seven eight nine ten

    * one two three four five six seven eight nine ten one two three four five
      six seven eight nine ten

  1. one two three four five six seven eight nine ten one two three four five
     six seven eight nine ten
"""
    content = Content("BSD-2-Clause")
    content.wrap("""```foobar
one two three four five six seven eight nine ten one two three four five six seven eight nine ten
```

one two three four five six seven eight nine ten one two three four five six seven eight nine ten
""")
    assert str(content) == """```foobar
one two three four five six seven eight nine ten one two three four five six seven eight nine ten
```

one two three four five six seven eight nine ten one two three four five six
seven eight nine ten
"""
    content = Content("BSD-2-Clause")
    content.wrap("""```not closed""")
    assert str(content) == """```not closed
"""
    content = Content("BSD-2-Clause")
    content.wrap([
        "```",
        "  the long long long long long long long long code "
        "the long long long long long long long long code",
        "",
        "```",
        "",
        "next",
        "",
        "```",
        "  more code"
        "```",
    ])
    assert str(content) == """```
  the long long long long long long long long code the long long long long long long long long code

```

next

```
  more code
```
"""
    content = Content("BSD-2-Clause")
    content.wrap(
        """- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

- abc
""")
    assert str(
        content
    ) == """- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

- abc
"""
    content = Content("BSD-2-Clause")
    content.wrap(
        """- xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
             def

- abc
""",
        initial_indent=" I ",
        subsequent_indent=" S ")
    assert str(
        content
    ) == """ I - xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
 S   def

 S - abc
"""


def test_iter():
    content = Content("BSD-2-Clause")
    assert "".join(content) == ""
    content.add("a")
    assert "".join(content) == "a"


def test_paste():
    content = Content("BSD-2-Clause")
    content.paste("")
    assert str(content) == ""
    content.paste("a")
    assert str(content) == """a
"""
    content.paste(["b", "c"])
    assert str(content) == """a b c
"""
    content.paste(content)
    assert str(content) == """a b c a b c
"""
    content = Content("BSD-2-Clause")
    content.paste("\n")
    assert str(content) == ""
    content.append(None)
    content.append("")
    content.paste("a")
    assert str(content) == """
a
"""
    content = Content("BSD-2-Clause")
    content.paste(["a", "b", "", "c"])
    assert str(content) == """a b

c
"""
    content = Content("BSD-2-Clause")
    content.paste(["a", "b", "", "  c"])
    assert str(content) == """a b

  c
"""


def test_add_blank_line():
    content = Content("BSD-2-Clause")
    content.add_blank_line()
    assert str(content) == """
"""


def test_add_list_empty():
    content = Content("BSD-2-Clause")
    content.add_list([], empty="empty")
    assert str(content) == """empty
"""


def test_ensure_blank_line():
    content = Content("BSD-2-Clause")
    content.ensure_blank_line()
    content.add("x")
    content.ensure_blank_line()
    content.add("y")
    assert str(content) == """x

y
"""


def test_indent_lines():
    content = Content("BSD-2-Clause")
    content.add_blank_line()
    content.append("x")
    content.indent_lines(3)
    assert str(content) == """
      x
"""


def test_indent():
    content = Content("BSD-2-Clause")
    with content.indent("A ", "a ", "a."):
        with content.indent("B ", "b ", "b."):
            with content.indent("C ", "c ", "c."):
                with content.indent("D ", "d ", "d."):
                    pass
        with content.indent("B ", "b ", "b."):
            with content.indent("C ", "c ", "c."):
                with content.indent("D ", "d ", "d."):
                    content.add("l")
                    content.add("m")
                    content.append("n")
                content.append("o")
            content.add("p")
            with content.indent("E ", "e ", "e."):
                content.add("q")
            with content.indent("F ", "f ", "f."):
                content.add("r")
                content.paste("s")
            with content.indent("G ", "g ", "g."):
                for i in range(100):
                    content.paste(str(i))
            with content.indent("H ", "h ", "h."):
                content.wrap([str(i) for i in range(100)])
            with content.indent("J ", "j ", "j."):
                content.wrap([str(i) for i in range(100)])
    assert str(content) == """A B C D l
a.b.c.d.
a b c d m
a b c d n
a b c o
a b p
a b E q
a b F r s
a b G 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
a b g 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51
a b g 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75
a b g 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
a b H 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
a b h 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51
a b h 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75
a b h 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
a b J 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
a b j 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51
a b j 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75
a b j 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
"""


def test_comment():
    content = Content("BSD-2-Clause")
    with content.comment_block():
        content.add(["abc", "", "def"])
    with content.comment_block():
        content.add(["ghi"])
    assert str(content) == """# abc
#
# def

# ghi
"""


def test_write(tmpdir):
    content = Content("BSD-2-Clause")
    content.append("x")
    path = os.path.join(tmpdir, "x", "y")
    content.write(path)
    with open(path, "r") as src:
        assert src.read() == """x
"""
    content.write(path, True)
    with open(path, "r") as src:
        assert src.read() == """x
"""
    tmpdir.chdir()
    path = "z"
    content.write(path)
    with open(path, "r") as src:
        assert src.read() == """x
"""


def test_make_lines():
    assert make_lines("a\nb") == ["a", "b"]
    assert make_lines(["c"]) == ["c"]
    content = Content("BSD-2-Clause")
    content.append("d")
    content.append("e")
    assert make_lines(content) == ["d", "e"]


def test_get_value():
    item_cache = EmptyItemCache()
    item = item_cache.add_item("/i", {"links": []})
    mapper = ItemMapper(item)
    value = {"term": "t"}
    ctx = ItemGetValueContext(item, "", "", value, mapper,
                              mapper.get_value_map, "", "", "plural")
    assert get_value_plural(ctx) == "ts"
    value["term"] = "ty"
    assert get_value_plural(ctx) == "ties"
    value["plural"] = "p"
    assert get_value_plural(ctx) == "p"
