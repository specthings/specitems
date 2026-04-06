# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the specdoc module. """

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

import os

from specitems.contentmarkdown import MarkdownContent, MarkdownMapper
from specitems.contentsphinx import SphinxContent, SphinxMapper
from specitems.items import ItemCache
from specitems.specdoc import (SpecDocumentConfig,
                               generate_specification_documentation)

from .util import create_item_cache_config


def test_document(tmpdir):
    item_cache_config = create_item_cache_config(tmpdir, "spec-doc")
    item_cache_config.spec_type_root_uid = "/root"
    item_cache = ItemCache(item_cache_config)
    root_type = item_cache["/root"]
    assert root_type.type == "spec"
    config = SpecDocumentConfig(root_type_uid="/root",
                                ignore="^f$",
                                section_label_prefix="SL")
    doc_target = os.path.join(tmpdir, "items.rst")
    config.target = doc_target
    generate_specification_documentation(config, item_cache,
                                         SphinxMapper(root_type),
                                         SphinxContent)

    md_doc_target = os.path.join(tmpdir, "items.md")
    config.target = md_doc_target
    generate_specification_documentation(config, item_cache,
                                         MarkdownMapper(root_type),
                                         MarkdownContent)

    with open(doc_target, "r") as src:
        content = """.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. _SLSpecificationItems:

Specification items
###################

.. _SLSpecificationItemHierarchy:

Specification item hierarchy
****************************

The specification item types have the following hierarchy:

- :ref:`SpecTypeRoot`

  - :ref:`SpecTypeA`

  - :ref:`SpecTypeB`

  - :ref:`SpecTypeGlossaryItemType`

    - :ref:`SpecTypeGlossaryTermItemType`

.. _SLSpecificationItemTypes:

Specification item types
************************

.. _SpecTypeRoot:

Root
====

A value of this type shall be of one of the following variants:

- The value may be a boolean. A reference to :ref:`SpecTypeRoot`. The value
  shall be ``true``.

- The value may be a set of attributes. All explicit attributes shall be
  specified. The explicit attributes for this type are:

  type
      The attribute value shall be a :ref:`SpecTypeName`.

  In addition to the explicit attributes, generic attributes may be specified.
  Each generic attribute key shall be a :ref:`SpecTypeName`. Each generic
  attribute value shall be a :ref:`SpecTypeRoot`.

- The value may be a floating-point number. The value shall be equal to ``0.0``.

- The value may be an integer number. The value shall be equal to ``0``.

- The value may be a list. Each list element shall be a :ref:`SpecTypeRoot`.

- There may be no value (null).

- The value may be a string. The value

  - shall meet,

    - shall contain an element of

      - "``a``",

      - "``b``", and

      - "``c``",

    - and, shall be equal to "``d``",

    - and, shall be greater than or equal to "``e``",

    - and, shall be greater than "``f``",

    - and, shall be an element of

      - "``g``", and

      - "``h``",

    - and, shall be less than or equal to "``i``",

    - and, shall be less than "``j``",

    - and, shall be not equal to "``k``",

    - and, shall match with the regular expression "``l``",

    - and, shall be ``true``,

    - and, shall be a valid item UID,

  - or,

    - shall be an element of,

    - or, shall be an element of

      - "``x``",

  - or, shall not meet,

    - shall not contain an element of

      - "``a``",

      - "``b``", and

      - "``c``",

    - or, shall be not equal to "``d``",

    - or, shall be less than "``e``",

    - or, shall be less than or equal to "``f``",

    - or, shall not be an element of

      - "``g``", and

      - "``h``",

    - or, shall be greater than "``i``",

    - or, shall be greater than or equal to "``j``",

    - or, shall be equal to "``k``",

    - or, shall not match with the regular expression "``l``",

    - or, shall be ``false``,

    - or, shall be an invalid item UID.

This type is refined by the following types:

- :ref:`SpecTypeA`

- :ref:`SpecTypeB`

- :ref:`SpecTypeGlossaryItemType`

This type is used by the following types:

- :ref:`SpecTypeRoot`

.. _SpecTypeA:

A
=

This type refines the :ref:`SpecTypeRoot` through the ``type`` attribute if the
value is ``spec``. A description.

The explicit attributes for this type are:

a
    The attribute value shall be an :ref:`SpecTypeA`.

c
    The attribute value shall be a :ref:`SpecTypeC`.

d
    The attribute value shall be a :ref:`SpecTypeD`.

This type is used by the following types:

- :ref:`SpecTypeA`

Please have a look at the following example:

.. code-block:: yaml

    a: null

.. _SpecTypeB:

B
=

This type refines the following types:

- :ref:`SpecTypeD` through the ``d1`` attribute if the value is ``b``

- :ref:`SpecTypeRoot` through the ``type`` attribute if the value is ``b``

Generic attributes may be specified. Each generic attribute key shall be a
:ref:`SpecTypeName`. Each generic attribute value shall be a list. Each list
element shall be a string.

.. _SpecTypeGlossaryItemType:

Glossary Item Type
==================

This type refines the :ref:`SpecTypeRoot` through the ``type`` attribute if the
value is ``glossary``. This set of attributes specifies a glossary item. All
explicit attributes shall be specified. The explicit attributes for this type
are:

glossary-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    glossary item type.

This type is refined by the following types:

- :ref:`SpecTypeGlossaryTermItemType`

.. _SpecTypeGlossaryTermItemType:

Glossary Term Item Type
=======================

This type refines the :ref:`SpecTypeGlossaryItemType` through the
``glossary-type`` attribute if the value is ``term``. This set of attributes
specifies a glossary term. All explicit attributes shall be specified. The
explicit attributes for this type are:

term
    The attribute value shall be a string. It shall be the glossary term.

text
    The attribute value shall be a string. It shall be the definition of the
    glossary term.

.. _SLSpecificationAttributeSetsAndValueTypes:

Specification attribute sets and value types
********************************************

.. _SpecTypeC:

C
=

Only the ``c`` attribute is mandatory. The explicit attributes for this type
are:

c
    The attribute value shall be a floating-point number.

This type is used by the following types:

- :ref:`SpecTypeA`

.. _SpecTypeD:

D
=

The following explicit attributes are mandatory:

- ``d1``

- ``d2``

The explicit attributes for this type are:

d1
    The attribute value shall be a :ref:`SpecTypeName`.

d2
    The attribute shall have no value.

This type is refined by the following types:

- :ref:`SpecTypeB`

This type is used by the following types:

- :ref:`SpecTypeA`

.. _SpecTypeName:

Name
====

The value shall be a string. It shall be an attribute name. The value shall
match with the regular expression
"``^([a-z][a-z0-9-]*|SPDX-License-Identifier)$``".

This type is used by the following types:

- :ref:`SpecTypeB`

- :ref:`SpecTypeD`

- :ref:`SpecTypeGlossaryItemType`

- :ref:`SpecTypeRoot`
"""
        assert content == src.read()

    with open(md_doc_target, "r") as src:
        content = """% SPDX-License-Identifier: CC-BY-SA-4.0

% Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG

% This file was automatically generated.  Do not edit it.

(SLSpecificationItems)=

# Specification items

(SLSpecificationItemHierarchy)=

## Specification item hierarchy

The specification item types have the following hierarchy:

- {ref}`SpecTypeRoot`

  - {ref}`SpecTypeA`

  - {ref}`SpecTypeB`

  - {ref}`SpecTypeGlossaryItemType`

    - {ref}`SpecTypeGlossaryTermItemType`

(SLSpecificationItemTypes)=

## Specification item types

(SpecTypeRoot)=

### Root

A value of this type shall be of one of the following variants:

- The value may be a boolean. A reference to {ref}`SpecTypeRoot`. The value
  shall be `true`.

- The value may be a set of attributes. All explicit attributes shall be
  specified. The explicit attributes for this type are:

  type
  : The attribute value shall be a {ref}`SpecTypeName`.

  In addition to the explicit attributes, generic attributes may be specified.
  Each generic attribute key shall be a {ref}`SpecTypeName`. Each generic
  attribute value shall be a {ref}`SpecTypeRoot`.

- The value may be a floating-point number. The value shall be equal to `0.0`.

- The value may be an integer number. The value shall be equal to `0`.

- The value may be a list. Each list element shall be a {ref}`SpecTypeRoot`.

- There may be no value (null).

- The value may be a string. The value

  - shall meet,

    - shall contain an element of

      - "`a`",

      - "`b`", and

      - "`c`",

    - and, shall be equal to "`d`",

    - and, shall be greater than or equal to "`e`",

    - and, shall be greater than "`f`",

    - and, shall be an element of

      - "`g`", and

      - "`h`",

    - and, shall be less than or equal to "`i`",

    - and, shall be less than "`j`",

    - and, shall be not equal to "`k`",

    - and, shall match with the regular expression "`l`",

    - and, shall be `true`,

    - and, shall be a valid item UID,

  - or,

    - shall be an element of,

    - or, shall be an element of

      - "`x`",

  - or, shall not meet,

    - shall not contain an element of

      - "`a`",

      - "`b`", and

      - "`c`",

    - or, shall be not equal to "`d`",

    - or, shall be less than "`e`",

    - or, shall be less than or equal to "`f`",

    - or, shall not be an element of

      - "`g`", and

      - "`h`",

    - or, shall be greater than "`i`",

    - or, shall be greater than or equal to "`j`",

    - or, shall be equal to "`k`",

    - or, shall not match with the regular expression "`l`",

    - or, shall be `false`,

    - or, shall be an invalid item UID.

This type is refined by the following types:

- {ref}`SpecTypeA`

- {ref}`SpecTypeB`

- {ref}`SpecTypeGlossaryItemType`

This type is used by the following types:

- {ref}`SpecTypeRoot`

(SpecTypeA)=

### A

This type refines the {ref}`SpecTypeRoot` through the `type` attribute if the
value is `spec`. A description.

The explicit attributes for this type are:

a
: The attribute value shall be an {ref}`SpecTypeA`.

c
: The attribute value shall be a {ref}`SpecTypeC`.

d
: The attribute value shall be a {ref}`SpecTypeD`.

This type is used by the following types:

- {ref}`SpecTypeA`

Please have a look at the following example:

```{code-block} yaml
a: null
```

(SpecTypeB)=

### B

This type refines the following types:

- {ref}`SpecTypeD` through the `d1` attribute if the value is `b`

- {ref}`SpecTypeRoot` through the `type` attribute if the value is `b`

Generic attributes may be specified. Each generic attribute key shall be a
{ref}`SpecTypeName`. Each generic attribute value shall be a list. Each list
element shall be a string.

(SpecTypeGlossaryItemType)=

### Glossary Item Type

This type refines the {ref}`SpecTypeRoot` through the `type` attribute if the
value is `glossary`. This set of attributes specifies a glossary item. All
explicit attributes shall be specified. The explicit attributes for this type
are:

glossary-type
: The attribute value shall be a {ref}`SpecTypeName`. It shall be the glossary
  item type.

This type is refined by the following types:

- {ref}`SpecTypeGlossaryTermItemType`

(SpecTypeGlossaryTermItemType)=

### Glossary Term Item Type

This type refines the {ref}`SpecTypeGlossaryItemType` through the
`glossary-type` attribute if the value is `term`. This set of attributes
specifies a glossary term. All explicit attributes shall be specified. The
explicit attributes for this type are:

term
: The attribute value shall be a string. It shall be the glossary term.

text
: The attribute value shall be a string. It shall be the definition of the
  glossary term.

(SLSpecificationAttributeSetsAndValueTypes)=

## Specification attribute sets and value types

(SpecTypeC)=

### C

Only the `c` attribute is mandatory. The explicit attributes for this type are:

c
: The attribute value shall be a floating-point number.

This type is used by the following types:

- {ref}`SpecTypeA`

(SpecTypeD)=

### D

The following explicit attributes are mandatory:

- `d1`

- `d2`

The explicit attributes for this type are:

d1
: The attribute value shall be a {ref}`SpecTypeName`.

d2
: The attribute shall have no value.

This type is refined by the following types:

- {ref}`SpecTypeB`

This type is used by the following types:

- {ref}`SpecTypeA`

(SpecTypeName)=

### Name

The value shall be a string. It shall be an attribute name. The value shall
match with the regular expression
"`^([a-z][a-z0-9-]*|SPDX-License-Identifier)$`".

This type is used by the following types:

- {ref}`SpecTypeB`

- {ref}`SpecTypeD`

- {ref}`SpecTypeGlossaryItemType`

- {ref}`SpecTypeRoot`
"""
        assert content == src.read()
