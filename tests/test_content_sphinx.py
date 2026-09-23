# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the contentsphinx module. """

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

from specitems import (COL_SPAN, ContentContext, EmptyItem, EmptyItemCache,
                       Item, ItemCache, ItemMapper, LicenseAggregate,
                       LicenseProvider, ROW_SPAN, SpecTypeProvider,
                       SphinxContent, SphinxMapper, augment_glossary_terms,
                       get_reference, make_label)

from .util import create_item_cache_config, get_other_type_data_by_uid


def test_sphinx_link():
    content = SphinxContent(context="CC-BY-SA-4.0")
    assert content.link("name", "target") == "`name <target>`__"


def test_sphinx_reference():
    content = SphinxContent(context="CC-BY-SA-4.0")
    assert content.reference("label") == ":ref:`label`"
    assert content.reference("label", "name") == ":ref:`name <label>`"


def test_special():
    content = SphinxContent(context="CC-BY-SA-4.0")
    assert content.code("text") == "``text``"
    assert content.emphasize("text") == "*text*"
    assert content.strong("text") == "**text**"
    assert content.path("te.xt") == ":file:`te.\u200bxt`"
    assert content.term("text") == ":term:`text`"
    assert content.term("text", "term") == ":term:`text <term>`"
    assert content.term("text", "text") == ":term:`text`"
    assert content.cite("identifier") == ":cite:`identifier`"
    assert content.escape(" !\"#$%&'()*+,-./0123456789:;<=>?"
                          "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
                          "abcdefghijklmnopqrstuvwxyz{|}~") == (
                              " !\"#$%&'()\\*+,-./0123456789:;<=>?"
                              "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^\\_\\`"
                              "abcdefghijklmnopqrstuvwxyz{\\|}~")


def test_add_label():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_label("x")
    assert str(content) == """.. _x:

"""


def test_label_scope():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.label_scope("x"):
        with content.section("y"):
            pass
    assert str(content) == ""
    with content.label_scope("x"):
        with content.section("y"):
            content.add("z")
    assert str(content) == """.. _xY:

y
#

z
"""


def test_directive():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.directive("x"):
        content.add("y")
    assert str(content) == """.. x::

    y
"""
    content.gap = False
    with content.directive("z", "xy", [":a:", ":b:"]):
        content.add("c")
    assert str(content) == """.. x::

    y

.. z:: xy
    :a:
    :b:

    c
"""


def test_add_header():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_header("x")
    assert str(content) == """x
#

"""
    content.add_header("yz", 1)
    assert str(content) == """x
#

yz
**

"""


def test_add_rubric():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_rubric("x")
    assert str(content) == """.. rubric:: x

"""


def test_get_reference():
    assert get_reference("a") == ":ref:`a`"
    assert get_reference("a", "b") == ":ref:`b <a>`"


def test_make_label():
    assert make_label("ab cd") == "AbCd"


def test_section():
    content = SphinxContent(context="CC-BY-SA-4.0")
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
    assert str(content) == """.. _AbCd:

ab cd
#####

AbCd

.. _AbCdEfGh:

ef gh
*****

AbCdEfGh

.. _AbCdEfGhmn:

ij kl
=====

AbCdEfGhmn
"""


def test_empty_sections():
    content = SphinxContent(context="CC-BY-SA-4.0")
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


def test_wrap():
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap("")
    assert str(content) == ""
    content.wrap("a")
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
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap("\n")
    assert str(content) == ""
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap(["a", "", "  b"])
    assert str(content) == """a

  b
"""
    content = SphinxContent(context="BSD-2-Clause")
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
    content = SphinxContent(context="BSD-2-Clause")
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
    content = SphinxContent(context="BSD-2-Clause")
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
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap("""```foobar
one two three four five six seven eight nine ten one two three four five six seven eight nine ten
```

one two three four five six seven eight nine ten one two three four five six seven eight nine ten
""")
    assert str(content) == """.. code-block:: foobar

    one two three four five six seven eight nine ten one two three four five six seven eight nine ten

one two three four five six seven eight nine ten one two three four five six
seven eight nine ten
"""
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap("""```not closed""")
    assert str(content) == """.. code-block:: not closed

"""
    content = SphinxContent(context="BSD-2-Clause")
    content.wrap("""`code`
_emphasize_
*strong*

``keep as is``
:ref:`keep as <is>`
`keep as <is>`__

{multi
line
role}`multi
line
text`
one `code` two
three _emphasize_ four
five *strong* six

one `more
code` two
three _more
emphasize_ four
five *more
strong* six
[red
yellow](green
blue)
""")
    assert str(content) == """``code`` *emphasize* **strong**

``keep as is`` :ref:`keep as <is>` `keep as <is>`__

:multi line role:`multi line text` one ``code`` two three *emphasize* four five
**strong** six

one ``more code`` two three *more emphasize* four five **more strong** six `red
yellow <green blue>`__
"""


def test_list_item():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.list_item("ab cd"):
        content.paste("ef gh")
        with content.list_item("ij kl"):
            content.add("mn op")
        content.paste("qr st")
    with content.list_item("uv"):
        pass
    content.add_list_item("wx")
    assert str(content) == """- ab cd ef gh

  - ij kl

    mn op

  qr st

- uv

- wx
"""


def test_add_list():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_list([], "a")
    assert str(content) == ""
    content.add_list(["b", "c"], "a", "d")
    assert str(content) == """a

- b

- c

d
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_list(["b", "c"])
    assert str(content) == """- b

- c
"""


def test_append():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.append("x")
    assert str(content) == """x
"""
    with content.indent():
        content.append("y")
        assert str(content) == """x
    y
"""
        content.append("")
        assert str(content) == """x
    y

"""


def test_add_image():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_image("abc")
    assert str(content) == """.. image:: abc
    :align: center

"""
    content.add_image("def", "50%")
    assert str(content) == """.. image:: abc
    :align: center

.. image:: def
    :align: center
    :width: 50%

"""


def test_latex_environment():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.latex_environment("env", use=False):
        content.add("abc")
    assert str(content) == "abc\n"
    with content.latex_environment("env"):
        content.add("def")
    assert str(content) == """abc

.. raw:: latex

    \\begin{env}

def

.. raw:: latex

    \\end{env}
"""


def test_latex_font_size():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.latex_font_size():
        pass
    with content.latex_font_size():
        content.add("abc")
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

abc

.. raw:: latex

    \\end{tiny}
"""


def test_latex_font_size_int():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.latex_font_size(-1):
        pass
    with content.latex_font_size(-1):
        content.add("abc")
    assert str(content) == """.. raw:: latex

    \\begin{small}

abc

.. raw:: latex

    \\end{small}
"""


def test_add_index_entries():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_index_entries(["x", "y"])
    assert str(content) == """.. index:: x
.. index:: y
"""
    content.add_index_entries("z")
    assert str(content) == """.. index:: x
.. index:: y

.. index:: z
"""


def test_add_definition_item():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_definition_item("x", ["y", "z"])
    assert str(content) == """x
    y z
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_definition_item("a", "\n b\n")
    assert str(content) == """a
    b
"""


def test_definition_item_with_directive():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add("term")
    with content.indent():
        with content.directive("code-block", "c"):
            content.add("int x;")
    assert str(content) == """term
    .. code-block:: c

        int x;
"""


def test_add_glossary_term():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_glossary_term("x", ["y", "z"])
    assert str(content) == """x
    y z
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_glossary_term("a", "\n b\n")
    assert str(content) == """a
    b
"""


def test_license():
    content = SphinxContent(
        context=ContentContext(LicenseAggregate("MIT", ["BSD-2-Clause"])))
    match = "permits neither the primary license MIT"
    with pytest.raises(ValueError, match=match):
        content.register_license("Apache-2.0")
    item = EmptyItem()
    item["SPDX-License-Identifier"] = "Apache-2.0"
    item["copyrights"] = []
    with pytest.raises(ValueError, match=match):
        content.register_license_and_copyrights_of_item(item)
    item["SPDX-License-Identifier"] = "MIT"
    item["copyrights"] = ["Copyright (C) A"]
    with pytest.raises(ValueError, match=r"Copyright \(C\) A"):
        content.register_license_and_copyrights_of_item(item)
    assert content.register_license("MIT OR BSD-2-Clause") == "MIT"
    assert content.register_license("BSD-2-Clause") == "BSD-2-Clause"
    bare = SphinxContent(context="MIT")
    bare.add_licence_and_copyrights()
    assert str(bare) == """.. SPDX-License-Identifier: MIT

"""
    content.register_copyright("Copyright (C) 2020 ACME")
    assert str(content) == ""
    content.add_licence_and_copyrights()
    assert str(content) == """.. SPDX-License-Identifier: MIT

.. Copyright (C) 2020 ACME

"""


def test_license_and_copyrights():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with pytest.raises(ValueError):
        content.register_license("x")
    content.register_copyright("Copyright (C) 123 A")
    assert str(content) == ""
    content.add_licence_and_copyrights()
    assert str(content) == """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 123 A

"""


def test_comment():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.comment_block():
        content.add(["abc", "", "def"])
    assert str(content) == """.. abc
..
.. def
"""


def test_simple_table():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_simple_table([])
    assert str(content) == ""
    content.add_simple_table([["a", "b"], ["cc", "ddd"]])
    assert str(content) == """.. table::
    :class: longtable

    == ===
    a  b
    == ===
    cc ddd
    == ===
"""


def test_simple_table_widths():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_simple_table([["a", "b"], ["cc", "ddd"]], [10, 90])
    assert str(content) == """.. table::
    :class: longtable
    :widths: 10,90

    == ===
    a  b
    == ===
    cc ddd
    == ===
"""


def test_simple_table_font_size():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_simple_table([["a", "b"], ["cc", "ddd"]], font_size=1)
    assert str(content) == """.. raw:: latex

    \\begin{large}

.. table::
    :class: longtable

    == ===
    a  b
    == ===
    cc ddd
    == ===

.. raw:: latex

    \\end{large}
"""


def test_grid_table():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_grid_table([], [])
    assert str(content) == ""
    content.add_grid_table([["a", "b"], ["cc", "ddd"]], widths=[50, 50])
    content.add_grid_table(
        [["1", "2", "3"], ["aa", "bbb", "cccc"], ["ddd", ROW_SPAN, "e"],
         ["ff", "g", "h"], [ROW_SPAN, "i", COL_SPAN],
         [ROW_SPAN, ROW_SPAN, ROW_SPAN | COL_SPAN]],
        widths=[30, 30, 40])
    assert str(content) == """.. table::
    :class: longtable
    :widths: 50,50

    +----+-----+
    | a  | b   |
    +====+=====+
    | cc | ddd |
    +----+-----+

.. table::
    :class: longtable
    :widths: 30,30,40

    +-----+-----+------+
    | 1   | 2   | 3    |
    +=====+=====+======+
    | aa  | bbb | cccc |
    +-----+     +------+
    | ddd |     | e    |
    +-----+-----+------+
    | ff  | g   | h    |
    +     +-----+------+
    |     | i          |
    +     +            +
    |     |            |
    +-----+-----+------+
"""


def test_grid_table_multiline_cells():
    # Multi-line cell: width = longest line, not total length.
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_grid_table(
        [["Parameter", "Description"], ["value", "A single-line description."],
         ["items", "First line of a two-line\ndescription that wraps."]])
    assert str(content) == """.. table::
    :class: longtable

    +-----------+----------------------------+
    | Parameter | Description                |
    +===========+============================+
    | value     | A single-line description. |
    +-----------+----------------------------+
    | items     | First line of a two-line   |
    |           | description that wraps.    |
    +-----------+----------------------------+
"""
    # Span must merge every line, not just the first; two tables since
    # combining needs an unsupported L-shaped merge.
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_grid_table([["1", "2", "3"], ["multi\nline", "x", COL_SPAN]],
                           widths=[30, 30, 40])
    assert str(content) == """.. table::
    :class: longtable
    :widths: 30,30,40

    +-------+---+---+
    | 1     | 2 | 3 |
    +=======+===+===+
    | multi | x     |
    | line  |       |
    +-------+---+---+
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_grid_table(
        [["1", "2", "3"], ["a", "b", "c"], ["multi\nline", ROW_SPAN, "y"]],
        widths=[30, 30, 40])
    assert str(content) == """.. table::
    :class: longtable
    :widths: 30,30,40

    +-------+---+---+
    | 1     | 2 | 3 |
    +=======+===+===+
    | a     | b | c |
    +-------+   +---+
    | multi |   | y |
    | line  |   |   |
    +-------+---+---+
"""


def test_substitute(tmpdir):
    config = create_item_cache_config(tmpdir, "spec-sphinx")
    item_cache = ItemCache(config,
                           type_provider=SpecTypeProvider(
                               get_other_type_data_by_uid()))
    augment_glossary_terms(item_cache["/g"], [])
    mapper = SphinxMapper(item_cache["/x"], "CC-BY-SA-4.0")
    match = (r"substitution in text of an unnamed item \(mapper spec:/x\) "
             r"using prefix '' failed in line 1 "
             r"of '\${x:/y}': KeyError: 'y'\n"
             r"  via cannot get value for '/y' of spec:/x specified by "
             r"'x:/y'\n  > 1: \${x:/y}\n       \^")
    with pytest.raises(ValueError, match=match):
        mapper.substitute("${x:/y}")
    assert mapper.substitute("${x:/term}") == ":term:`y`"
    assert mapper.substitute("${x:/plural}") == ":term:`ies <y>`"
    assert mapper.substitute("${xs:/term}") == ":term:`xs <Sub - xs>`"
    mapper.item.view["term"] = "foobar"
    assert mapper.substitute("${x:/term}") == ":term:`y <foobar>`"
    assert mapper.substitute("${z:/plural}") == ":term:`zs <z>`"
    mapper.add_get_value("other:/name", lambda ctx: ctx.value[ctx.key])
    assert mapper.substitute("${y:/name}") == "foobar"
    context = ContentContext(LicenseAggregate("BSD-2-Clause"))
    mapper = SphinxMapper(item_cache["/x"], context)
    mapper.substitute("${x:/term}")
    assert context.licenses.copyrights_of("BSD-2-Clause").get_statements()
    context = ContentContext(LicenseAggregate("MIT"))
    mapper = SphinxMapper(item_cache["/x"], context)
    with pytest.raises(ValueError, match="permits neither"):
        mapper.substitute("${x:/term}")
    context = ContentContext(LicenseAggregate("BSD-2-Clause"))
    work = context.for_work("/w")
    mapper = SphinxMapper(item_cache["/x"], context)
    with mapper.work(work):
        mapper.substitute("${x:/term}")
    assert work.licenses.copyrights_of("BSD-2-Clause").get_statements()
    assert not context.licenses
    mapper.substitute("${x:/term}")
    assert context.licenses
    with ItemMapper(item_cache["/x"]).work(work):
        pass


def test_add_code_block():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_code_block([])
    assert str(content) == ""
    content.add_code_block([""])
    content.add_code_block([" a"], line_number_start=99)
    content.add_code_block(["c"],
                           language="language",
                           font_size=0,
                           line_number_start=-1)
    assert str(content) == """.. raw:: latex

    \\begin{footnotesize}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​

.. raw:: latex

    \\end{footnotesize}

.. raw:: latex

    \\begin{footnotesize}

.. code-block:: none
    :linenos:
    :lineno-start: 99

    ​ a

.. raw:: latex

    \\end{footnotesize}

.. raw:: latex

    \\begin{normalsize}

.. code-block:: language

    c

.. raw:: latex

    \\end{normalsize}
"""


def test_add_program_output():
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output([], [])
    assert str(content) == ""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output(["€"], [], "label")
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

.. _label0:

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​\​x​2​0​a​c

.. raw:: latex

    \\end{tiny}
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output(["x", "y"], [(0, 1)], "label")
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

.. _label0:

.. code-block:: none
    :linenos:
    :lineno-start: 1

    [... data lines not shown in report ...]

.. code-block:: none
    :linenos:
    :lineno-start: 2

    ​y

.. raw:: latex

    \\end{tiny}
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output(["x", "y"], [(0, 1)])
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    [... data lines not shown in report ...]

.. code-block:: none
    :linenos:
    :lineno-start: 2

    ​y

.. raw:: latex

    \\end{tiny}
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output(
        list(str(i) for i in range(150)) + ["x"], [(0, 150)], "label")
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

.. _label0:

.. code-block:: none
    :linenos:
    :lineno-start: 1

    [... data lines not shown in report ...]

.. _label100:

.. code-block:: none
    :linenos:
    :lineno-start: 151

    ​x

.. raw:: latex

    \\end{tiny}
"""
    content = SphinxContent(context="CC-BY-SA-4.0")
    content.add_program_output([
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "0", "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "01234567890123456789012345678901234567890123456789"
        "0123456789012345678901234567890123456789012345678€"
        "0"
    ], [], "label")
    assert str(content) == """.. raw:: latex

    \\begin{tiny}

.. _label0:

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​[​.​.​.​ ​m​o​r​e​ ​d​a​t​a​ ​n​o​t​ ​s​h​o​w​n​ ​i​n​ ​r​e​p​o​r​t​ ​.​.​.​]
    ​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​9​0​1​2​3​4​5​6​7​8​[​.​.​.​ ​m​o​r​e​ ​d​a​t​a​ ​n​o​t​ ​s​h​o​w​n​ ​i​n​ ​r​e​p​o​r​t​ ​.​.​.​]

.. raw:: latex

    \\end{tiny}
"""


def test_topic_as_rubric():
    content = SphinxContent(context="CC-BY-SA-4.0")
    with content.topic("Parameters"):
        content.add("param")
    assert str(content) == """.. rubric:: PARAMETERS:

param
"""


def test_topic_as_definition():
    content = SphinxContent(context="CC-BY-SA-4.0", topic_as_definition=True)
    with content.topic("Parameters"):
        with content.directive("code-block", "c"):
            content.add("int x;")
    with content.topic("Description"):
        content.add("A description.")
    assert str(content) == """Parameters
    .. code-block:: c

        int x;

Description
    A description.
"""


def test_context_balance_on_exception():
    # Each context restores its state even where the body raises.  The label
    # stack, the section stack and the line context stack are then ready for
    # the next section.
    contexts = (
        lambda c: c.indent(),
        lambda c: c.indent(levels=3),
        lambda c: c.comment_block(),
        lambda c: c.list_item("item"),
        lambda c: c.label_scope("Scope"),
        lambda c: c.topic("Name"),
        lambda c: c.section("Sec"),
        lambda c: c.directive("note"),
        lambda c: c.latex_environment("small"),
    )
    for open_context in contexts:
        content = SphinxContent(context="CC-BY-SA-4.0")
        with pytest.raises(RuntimeError):
            with open_context(content):
                raise RuntimeError("boom")
        assert content.get_label() == ""
        text = str(content)
        assert text.count("\\begin{") == text.count("\\end{")
        with content.section("Next") as label:
            content.add("body")
        assert label == "Next"
        assert str(content).endswith("""Next
####

body
""")


def test_fragment():
    content = SphinxContent(2, context=ContentContext("MIT", ["x"]))
    fragment = content.fragment()
    assert isinstance(fragment, SphinxContent)
    assert fragment.context is content.context
    assert not str(fragment)
    fragment.register_copyright("Copyright (C) 2020 ACME")
    assert content.context.licenses.copyrights_of().get_statements() == [
        "Copyright (C) 2020 ACME"
    ]


def test_for_work():
    context = ContentContext(LicenseAggregate("MIT", ["BSD-2-Clause"], "task"),
                             "Do not edit.")
    work = context.for_work("/f/a")
    assert work.licenses.name == "/f/a"
    assert work.licenses.primary == "MIT"
    assert work.licenses.accepted == ["BSD-2-Clause"]
    assert work.automatically_generated_warning == "Do not edit."
    assert work.licenses is not context.licenses
    other = context.for_work("/f/b", "BSD-2-Clause")
    assert other.licenses.primary == "BSD-2-Clause"


def test_license_text():
    context = ContentContext(LicenseAggregate("MIT"))
    with pytest.raises(ValueError, match="states no license presentation"):
        context.license_text()
    provider = LicenseProvider([])
    with pytest.raises(ValueError, match="no item states the license MIT"):
        ContentContext(LicenseAggregate("MIT"), None, provider).license_text()


def test_check_license_items():
    context = ContentContext(LicenseAggregate("MIT", ["BSD-2-Clause"], "/w"))
    with pytest.raises(ValueError) as err:
        context.check_license_items()
    assert str(err.value) == "the work /w states no license presentation"
    item = Item(
        EmptyItemCache(), "/l/mit", {
            "identifier": "MIT",
            "name": "The MIT License",
            "reproduce-text": False,
            "text": None,
            "uri": None,
        })
    item.type = "license"
    context = ContentContext(context.licenses, None, LicenseProvider([item]))
    with pytest.raises(ValueError) as err:
        context.check_license_items()
    assert str(err.value) == ("no item states a license which the work /w "
                              "may take: BSD-2-Clause")
    ContentContext(LicenseAggregate("MIT"), None,
                   LicenseProvider([item])).check_license_items()
