# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the contentcommonmark module. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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

from specitems import (COL_SPAN, CommonMarkContent, CommonMarkMapper,
                       ItemCache, ROW_SPAN, SpecTypeProvider)

from .util import create_item_cache_config, get_other_type_data_by_uid


def test_commonmark_link():
    content = CommonMarkContent()
    assert content.link("name", "target") == "[name](target)"


def test_commonmark_reference():
    content = CommonMarkContent()
    assert content.reference("label") == "[label](#label)"
    assert content.reference("label", "name") == "[name](#label)"


def test_commonmark_special():
    content = CommonMarkContent()
    assert content.code("text") == "`text`"
    assert content.emphasize("text") == "_text_"
    assert content.strong("text") == "*text*"
    assert content.path("text") == "`text`"
    assert content.term("text") == "text"
    assert content.term("text", "term") == "text"
    assert content.term("text", "text") == "text"
    assert content.cite("identifier") == ""
    assert content.escape(" !\"#$%&'()*+,-./0123456789:;<=>?"
                          "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
                          "abcdefghijklmnopqrstuvwxyz{|}~") == (
                              " !\"#\\$%&'()\\*+,-./0123456789:;\\<=>?"
                              "@ABCDEFGHIJKLMNOPQRSTUVWXYZ\\[\\\\\\]^\\_\\`"
                              "abcdefghijklmnopqrstuvwxyz{|}~")


def test_commonmark_header():
    content = CommonMarkContent()
    content.add_header("header")
    content.add_header("header", level=5, label="label")
    assert str(content) == """# header

<a id="label"></a>

###### header

"""


def test_commonmark_add_image():
    content = CommonMarkContent()
    content.add_image("abc")
    assert str(content) == """![](abc)
"""
    content.add_image("def", "50%")
    assert str(content) == """![](abc)

![](def)
"""


def test_commonmark_latex_environment():
    content = CommonMarkContent()
    with content.latex_environment("env", use=False):
        content.add("abc")
    assert str(content) == "abc\n"
    with content.latex_environment("env"):
        content.add("def")
    assert str(content) == """abc

```raw
\\begin{env}
```

def

```raw
\\end{env}
```
"""


def test_commonmark_latex_font_size():
    content = CommonMarkContent()
    with content.latex_font_size():
        pass
    with content.latex_font_size():
        content.add("abc")
    assert str(content) == """```raw
\\begin{tiny}
```

abc

```raw
\\end{tiny}
```
"""


def test_latex_font_size_int():
    content = CommonMarkContent()
    with content.latex_font_size(-1):
        pass
    with content.latex_font_size(-1):
        content.add("abc")
    assert str(content) == """```raw
\\begin{small}
```

abc

```raw
\\end{small}
```
"""


def test_mark_index_entries():
    content = CommonMarkContent()
    content.add_index_entries([])
    content.add_index_entries(["foo", "bar"])
    content.add_index_entries(["blub"])
    assert str(content) == ""


def test_commonmark_section():
    content = CommonMarkContent()
    assert content.get_sections() == []
    with content.section("ab cd") as label:
        assert content.get_sections() == ["ab cd"]
        content.add(label)
        with content.section("ef gh") as label2:
            assert content.get_sections() == ["ab cd", "ef gh"]
            content.add(label2)
            with content.section("ij kl", "mn") as label2:
                assert content.get_sections() == ["ab cd", "ef gh", "ij kl"]
                content.add(label2)
            assert content.get_sections() == ["ab cd", "ef gh"]
        assert content.get_sections() == ["ab cd"]
    assert content.get_sections() == []
    assert str(content) == """<a id="AbCd"></a>

# ab cd

AbCd

<a id="AbCdEfGh"></a>

## ef gh

AbCdEfGh

<a id="AbCdEfGhmn"></a>

### ij kl

AbCdEfGhmn
"""


def test_commonmark_empty_sections():
    content = CommonMarkContent()
    assert content.get_sections() == []
    with content.section("x"):
        with content.section("y"):
            with content.section("z"):
                with content.indent():
                    pass
    assert str(content) == ""
    content.paste("a")
    content.paste("b")
    assert str(content) == "a b\n"
    with content.section("x"):
        with content.section("y"):
            with content.section("z"):
                with content.indent():
                    pass
    assert str(content) == "a b\n"
    content.paste("c")
    assert str(content) == "a b c\n"
    with content.section("x"):
        with content.section("y"):
            with content.section("z"):
                with content.indent():
                    pass
    assert str(content) == "a b c\n"
    content.add("d")
    assert str(content) == "a b c\n\nd\n"


def test_commonmark_rubric():
    content = CommonMarkContent()
    content.add_rubric("name")
    assert str(content) == """*name*

"""


def test_commonmark_directive():
    content = CommonMarkContent()
    with content.directive("directive", options=["option"]):
        content.add("text")
    with content.directive("foo", "bar"):
        content.add("line")
    assert str(content) == """```directive
text
```

```foo
line
```
"""


def test_commonmark_definition_list():
    content = CommonMarkContent()
    content.add_definition_item("item", [
        "def 0", "def 1",
        "0123456789012345678901234567890123456789012345678901234567890123456789",
        "0123456789012345678901234567890123456789"
    ])
    assert str(content) == """*item*:
def 0
def 1
0123456789012345678901234567890123456789012345678901234567890123456789
0123456789012345678901234567890123456789
"""


def test_commonmark_glossary_term():
    content = CommonMarkContent()
    content.add_glossary_term("term", "def 0\ndef 1")
    assert str(content) == """*term*:
def 0
def 1
"""


def test_commonmark_simple_table():
    content = CommonMarkContent()
    content.add_simple_table([])
    assert str(content) == ""
    content.add_simple_table([["a", "b"], ["cc", "d|dd"]])
    assert str(content) == """ | a   | b     |
 | --- | ----- |
 | cc  | d\\|dd |
"""
    content.add_simple_table([["a", "b"], ["cc", "ddd"]], font_size=0)
    assert str(content) == """ | a   | b     |
 | --- | ----- |
 | cc  | d\\|dd |

 | a   | b   |
 | --- | --- |
 | cc  | ddd |
"""


def test_commonmark_grid_table():
    content = CommonMarkContent()
    content.add_grid_table([], [])
    assert str(content) == ""
    content.add_grid_table([["a", "b"], ["cc", "ddd"]], widths=[50, 50])
    content.add_grid_table(
        [["1", "2", "3"], ["aa", "bbb", "cccc"], ["ddd", ROW_SPAN, "e"],
         ["ff", "g", "h"], [ROW_SPAN, "i", COL_SPAN],
         [ROW_SPAN, ROW_SPAN, ROW_SPAN | COL_SPAN]],
        widths=[30, 30, 40])
    assert str(content) == """<table>
  <tr><th>a</th><th>b</th></tr>
  <tr><td>cc</td><td>ddd</td></tr>
</table>
<table>
  <tr><th>1</th><th>2</th><th>3</th></tr>
  <tr><td>aa</td><td rowspan="2">bbb</td><td>cccc</td></tr>
  <tr><td>ddd</td><td>e</td></tr>
  <tr><td rowspan="3">ff</td><td>g</td><td>h</td></tr>
  <tr><td rowspan="2" colspan="2">i</td></tr>
  <tr></tr>
</table>
"""


def test_substitute(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-sphinx")
    item_cache = ItemCache(config,
                           type_provider=SpecTypeProvider(
                               get_other_type_data_by_uid()))
    mapper = CommonMarkMapper(item_cache["/x"])
    match = r"substitution for spec:/x using prefix '' failed for text:\n1: \${x:/y}"
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${x:/y}")
    assert mapper.substitute("${x:/term}") == "y"
    assert mapper.substitute("${x:/plural}") == "ies"
    assert mapper.substitute("${xs:/term}") == "xs"
    assert mapper.substitute("${z:/plural}") == "zs"
    mapper.add_get_value("other:/name", lambda ctx: ctx.value[ctx.key])
    assert mapper.substitute("${y:/name}") == "foobar"


def test_add_code_block():
    content = CommonMarkContent()
    content.add_code_block([])
    assert str(content) == """```none
```
"""
    content.add_code_block([""])
    content.add_code_block([" a"], line_number_start=99)
    content.add_code_block(["c"],
                           language="language",
                           font_size=0,
                           line_number_start=-1)
    assert str(content) == """```none
```

```none

```

```none
 a
```

```language
c
```
"""
