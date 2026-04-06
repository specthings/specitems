# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the contentmarkdown module. """

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

from specitems.contentmarkdown import MarkdownContent, MarkdownMapper
from specitems.glossary import augment_glossary_terms
from specitems.items import ItemCache, SpecTypeProvider

from .util import create_item_cache_config, get_other_type_data_by_uid


def test_markdown_get_reference():
    content = MarkdownContent()
    assert content.get_reference("label") == "{ref}`label`"
    assert content.get_reference("label", "name") == "{ref}`name <label>`"


def test_markdown_special():
    content = MarkdownContent()
    assert content.code("text") == "`text`"
    assert content.emphasize("text") == "_text_"
    assert content.strong("text") == "*text*"
    assert content.path("text") == "`text`"
    assert content.term("text") == "{term}`text`"
    assert content.term("text", "term") == "{term}`text <term>`"
    assert content.term("text", "text") == "{term}`text`"
    assert content.cite("identifier") == "{cite}`identifier`"
    assert content.escape(" !\"#$%&'()*+,-./0123456789:;<=>?"
                          "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
                          "abcdefghijklmnopqrstuvwxyz{|}~") == (
                              " !\"#\\$%&'()\\*+,-./0123456789:;\\<=>?"
                              "@ABCDEFGHIJKLMNOPQRSTUVWXYZ\\[\\\\\\]^\\_\\`"
                              "abcdefghijklmnopqrstuvwxyz{|}~")


def test_markdown_header():
    content = MarkdownContent()
    content.add_header("header")
    content.add_header("header", level=6, label="label")
    assert str(content) == """# header

(label)=

###### header

"""
    assert content.beautify() == """# header

(label)=

###### header
"""


def test_markdown_latex_environment():
    content = MarkdownContent()
    with content.latex_environment("env", use=False):
        content.add("abc")
    assert str(content) == "abc\n"
    with content.latex_environment("env"):
        content.add("def")
    assert str(content) == """abc

```{raw} latex
\\begin{env}
```

def

```{raw} latex
\\end{env}
```
"""


def test_markdown_latex_font_size():
    content = MarkdownContent()
    with content.latex_font_size():
        pass
    with content.latex_font_size():
        content.add("abc")
    assert str(content) == """```{raw} latex
\\begin{tiny}
```

abc

```{raw} latex
\\end{tiny}
```
"""


def test_latex_font_size_int():
    content = MarkdownContent()
    with content.latex_font_size(-1):
        pass
    with content.latex_font_size(-1):
        content.add("abc")
    assert str(content) == """```{raw} latex
\\begin{small}
```

abc

```{raw} latex
\\end{small}
```
"""


def test_mark_index_entries():
    content = MarkdownContent()
    content.add_index_entries([])
    content.add_index_entries(["foo", "bar"])
    content.add_index_entries(["blub"])
    assert str(content) == """```{index} foo
```

```{index} bar
```

```{index} blub
```
"""
    assert content.beautify() == """```{index} foo
```

```{index} bar
```

```{index} blub
```
"""


def test_markdown_section():
    content = MarkdownContent()
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
    assert str(content) == """(AbCd)=

# ab cd

AbCd

(AbCdEfGh)=

## ef gh

AbCdEfGh

(AbCdEfGhmn)=

### ij kl

AbCdEfGhmn
"""


def test_markdown_empty_sections():
    content = MarkdownContent()
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


def test_markdown_rubric():
    content = MarkdownContent()
    content.add_rubric("name")
    assert str(content) == """```{eval-rst}
.. rubric:: name
```

"""
    assert content.beautify() == """```{eval-rst}
.. rubric:: name
```
"""


def test_markdown_directive():
    content = MarkdownContent()
    with content.directive("directive", options=["option"]):
        content.add("text")
    with content.directive("foo", "bar"):
        content.add("line")
    assert str(content) == """```{directive}
option
text
```

```{foo} bar
line
```
"""
    assert content.beautify() == """```{directive}
option
text
```

```{foo} bar
line
```
"""


def test_markdown_definition_list():
    content = MarkdownContent()
    content.add_definition_item("item", [
        "def 0", "def 1",
        "0123456789012345678901234567890123456789012345678901234567890123456789",
        "0123456789012345678901234567890123456789"
    ])
    assert str(content) == """item
: def 0
  def 1
  0123456789012345678901234567890123456789012345678901234567890123456789
  0123456789012345678901234567890123456789
"""
    assert content.beautify() == """item
: def 0 def 1
  0123456789012345678901234567890123456789012345678901234567890123456789
  0123456789012345678901234567890123456789
"""


def test_markdown_glossary_term():
    content = MarkdownContent()
    with content.directive("glossary"):
        content.add_glossary_term("term", "def 0\ndef 1")
    assert str(content) == """```{glossary}
term

  def 0 def 1
```
"""
    assert content.beautify() == """```{glossary}
term

  def 0 def 1
```
"""


def test_markdown_beautify():
    content = MarkdownContent()
    content.add("""* a
 * b
  * c

    * d. dd. ddd.
      e.
      f

      * g

        h

      * i

      * j
    * k
   * l
  * m
 * n
* o

p

* q
* r

s. ss.  sss.
""")
    assert content.beautify() == """- a

- b

- c

  - d. dd. ddd. e. f

    - g

      h

    - i

    - j

  - k

- l

- m

- n

- o

p

- q
- r

s. ss. sss.
"""


def test_substitute(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-sphinx")
    item_cache = ItemCache(config,
                           type_provider=SpecTypeProvider(
                               get_other_type_data_by_uid()))
    augment_glossary_terms(item_cache["/g"], [])
    mapper = MarkdownMapper(item_cache["/x"])
    match = r"substitution for spec:/x using prefix '' failed for text:\n    1: \${x:/y}"
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${x:/y}")
    assert mapper.substitute("${x:/term}") == "{term}`y`"
    assert mapper.substitute("${x:/plural}") == "{term}`ies <y>`"
    assert mapper.substitute("${xs:/term}") == "{term}`xs <Sub - xs>`"
    assert mapper.substitute("${z:/plural}") == "{term}`zs <z>`"
    mapper.add_get_value("other:/name", lambda ctx: ctx.value[ctx.key])
    assert mapper.substitute("${y:/name}") == "foobar"


def test_add_code_block():
    content = MarkdownContent()
    content.add_code_block([])
    assert str(content) == ""
    content.add_code_block([""])
    content.add_code_block([" a"], line_number_start=99)
    content.add_code_block(["c"],
                           language="language",
                           font_size=0,
                           line_number_start=-1)
    assert str(content) == """```{code} none
:linenos:
:lineno-start: 1

```

```{code} none
:linenos:
:lineno-start: 99
 a
```

```{code} language
c
```
"""
