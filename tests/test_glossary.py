# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the glossary module. """

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

import functools
import os

from specitems.contentmarkdown import MarkdownContent, MarkdownMapper
from specitems.contentsphinx import SphinxContent, SphinxMapper
from specitems.glossary import (_GLOSSARY_PATH, DocumentGlossaryConfig,
                                GlossaryConfig, augment_glossary_terms,
                                generate_glossary)
from specitems.items import EmptyItemCache, ItemCache, SpecTypeProvider

from .util import create_item_cache_config


def test_empty_glossary():
    generate_glossary(GlossaryConfig(), [], EmptyItemCache(),
                      functools.partial(SphinxContent, 1))


def test_glossary(tmpdir):
    item_cache_config = create_item_cache_config(tmpdir, "spec-glossary")
    item_cache = ItemCache(item_cache_config,
                           type_provider=SpecTypeProvider({}))

    doc = DocumentGlossaryConfig(md_source_paths=[str(tmpdir)],
                                 rest_source_paths=[str(tmpdir)])
    glossary_config = GlossaryConfig(project_header="Project Glossary",
                                     project_groups=["/g"],
                                     documents=[doc])
    glossary_item = item_cache["/g"]
    augment_glossary_terms(glossary_item, [])

    project_glossary = os.path.join(tmpdir, "project", "glossary.rst")
    glossary_config.project_target = project_glossary
    document_glossary = os.path.join(tmpdir, "document", "glossary.rst")
    doc.target = document_glossary
    mapper = SphinxMapper(glossary_item)
    mapper.add_get_value("glossary/term:/foobar", lambda x: "foobar")
    generate_glossary(glossary_config, item_cache, mapper,
                      functools.partial(SphinxContent, 1))

    md_project_glossary = os.path.join(tmpdir, "project", "glossary.md")
    glossary_config.project_target = md_project_glossary
    md_document_glossary = os.path.join(tmpdir, "document", "glossary.md")
    doc.target = md_document_glossary
    md_mapper = MarkdownMapper(glossary_item)
    md_mapper.add_get_value("glossary/term:/foobar", lambda x: "foobar")
    generate_glossary(glossary_config, item_cache, md_mapper, MarkdownContent)

    with open(project_glossary, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG

.. _ProjectGlossary:

Project Glossary
****************

.. glossary::

    Not so General - x
        Term text X.

    T
        Term *text* $:term:`U` :term:`T` term.

        foobar

    U
        Term text U.

    V
        Term text V.  See also :term:`x <Not so General - x>`.
"""
        assert content == src.read()

    with open(document_glossary, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020 embedded brains GmbH & Co. KG

.. _Glossary:

Glossary
********

.. glossary::

    T
        Term *text* $:term:`U` :term:`T` term.

        foobar

    U
        Term text U.
"""
        assert content == src.read()

    with open(md_project_glossary, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020, 2023 embedded brains GmbH & Co. KG

(ProjectGlossary)=

# Project Glossary

```{glossary}
Not so General - x

  Term text X.

T

  Term _text_ ${term}`U` {term}`T` term.

  foobar

U

  Term text U.

V

  Term text V. See also {term}`x <Not so General - x>`.
```
"""
        assert content == src.read()

    with open(md_document_glossary, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020 embedded brains GmbH & Co. KG

(Glossary)=

# Glossary

```{glossary}
T

  Term _text_ ${term}`U` {term}`T` term.

  foobar

U

  Term text U.
```
"""
        assert content == src.read()


def _add_late_term(item_cache, uid, group, term):
    late = item_cache.add_item(
        uid, {
            "SPDX-License-Identifier": "CC-BY-SA-4.0",
            "copyrights": ["Copyright (C) 2020 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "glossary-type": "term",
            "links": [{
                "role": "glossary-member",
                "uid": group
            }],
            "term": term,
            "text": f"Term text {term}.\n",
            "type": "glossary"
        })
    item_cache.reinitialize_links()
    return late


def test_glossary_term_added_after_augment(tmpdir):
    """
    A member which arrives after the augmentation reads the path prefix of its
    group.
    """
    item_cache_config = create_item_cache_config(tmpdir, "spec-glossary")
    item_cache = ItemCache(item_cache_config,
                           type_provider=SpecTypeProvider({}))
    glossary_item = item_cache["/g"]
    augment_glossary_terms(glossary_item, [])

    top = _add_late_term(item_cache, "/glossary/late", "../g", "Late")
    assert top.view["term"] == "Late"
    assert top.view.get("term") == "Late"

    sub = _add_late_term(item_cache, "/glossary/sub/late", "g", "SubLate")
    assert sub.view["term"] == "Not so General - SubLate"
    assert sub.view.get("term") == "Not so General - SubLate"

    # A member of a group outside the augmented tree keeps its plain term.
    other_group = item_cache.add_item(
        "/other/g", {
            "SPDX-License-Identifier": "CC-BY-SA-4.0",
            "copyrights": ["Copyright (C) 2020 embedded brains GmbH & Co. KG"],
            "enabled-by": True,
            "glossary-type": "group",
            "links": [],
            "name": "Other",
            "text": "Text.\n",
            "type": "glossary"
        })
    assert other_group.view.get(_GLOSSARY_PATH) is None
    other = _add_late_term(item_cache, "/other/late", "g", "Other")
    assert other.view["term"] == "Other"

    mapper = SphinxMapper(glossary_item)
    assert mapper.substitute(
        "${/glossary/sub/late:/term}",
        glossary_item) == (":term:`SubLate <Not so General - SubLate>`")
    assert mapper.substitute(
        "${/glossary/sub/late:/plural}",
        glossary_item) == (":term:`SubLates <Not so General - SubLate>`")

    doc = DocumentGlossaryConfig(md_source_paths=[str(tmpdir)],
                                 rest_source_paths=[str(tmpdir)])
    glossary_config = GlossaryConfig(project_header="Project Glossary",
                                     project_groups=["/g"],
                                     documents=[doc])
    glossary_config.project_target = os.path.join(tmpdir, "project",
                                                  "glossary.rst")
    doc.target = os.path.join(tmpdir, "document", "glossary.rst")
    mapper.add_get_value("glossary/term:/foobar", lambda x: "foobar")
    generate_glossary(glossary_config, item_cache, mapper,
                      functools.partial(SphinxContent, 1))

    with open(glossary_config.project_target, "r") as src:
        content = src.read()
        assert "Not so General - SubLate" in content
        assert "\n    Late\n" in content
