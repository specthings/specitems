.. SPDX-License-Identifier: CC-BY-SA-4.0

.. Copyright (C) 2019, 2026 embedded brains GmbH & Co. KG

.. This file was automatically generated.  Do not edit it.

.. _SpecificationItems:

Specification items
###################

.. _SpecificationItemHierarchy:

Specification item hierarchy
****************************

The specification item types have the following hierarchy:

- :ref:`SpecTypeRootItemType`

  - :ref:`SpecTypeGlossaryItemType`

    - :ref:`SpecTypeGlossaryGroupItemType`

    - :ref:`SpecTypeGlossaryTermItemType`

  - :ref:`SpecTypeProxyItemType`

  - :ref:`SpecTypeReference`

    - :ref:`SpecTypeArticleReference`

    - :ref:`SpecTypeBookReference`

    - :ref:`SpecTypeBookletReference`

    - :ref:`SpecTypeConferenceProceedingsReference`

    - :ref:`SpecTypeInBookReference`

    - :ref:`SpecTypeInCollectionReference`

    - :ref:`SpecTypeInConferenceProceedingsReference`

    - :ref:`SpecTypeManualReference`

    - :ref:`SpecTypeMastersOrPhDThesisReference`

    - :ref:`SpecTypeMiscellaneousReference`

    - :ref:`SpecTypeTechnicalReportReference`

  - :ref:`SpecTypeSpecificationItemType`

.. _SpecificationItemTypes:

Specification item types
************************

.. _SpecTypeRootItemType:

Root Item Type
==============

This is the root specification item type.

Specification items consist of a defined set of key-value pairs called
attributes.  Each attribute key name shall be a :ref:`SpecTypeName`.  Item
attributes may have dictionary, list, integer, floating-point number, and
string values or a combination of them.  The format of items is defined by the
type hierarchy rooting in this type.

The ``type`` attribute allows a specialization into domain-specific type
hierarchies.  For example, for a software specification possible type
refinements may be created to specify requirements, specializations of
requirements, interfaces, test suites, test cases, and requirement validations.

The specification items may be stored in or loaded from files in JSON or YAML
format. All explicit attributes shall be specified. The explicit attributes for
this type are:

SPDX-License-Identifier
    The attribute value shall be a :ref:`SpecTypeSPDXLicenseIdentifier`. It
    shall be the license of the item.

copyrights
    The attribute value shall be a list. Each list element shall be a
    :ref:`SpecTypeCopyright`. It shall be the list of copyright statements of
    the item.

enabled-by
    The attribute value shall be an :ref:`SpecTypeEnabledByExpression`. It
    shall define the conditions under which the item is enabled.

links
    The attribute value shall be a list. Each list element shall be a
    :ref:`SpecTypeLink`.

type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the item
    type.  The selection of types and the level of detail depends on a
    particular standard and product model.  We need enough flexibility to be in
    line with the European Cooperation for Space Standardization standard
    ECSS-E-ST-10-06 and possible future applications of other standards.  This
    attribute is used for type refinements.

This type is refined by the following types:

- :ref:`SpecTypeGlossaryItemType`

- :ref:`SpecTypeProxyItemType`

- :ref:`SpecTypeReference`

- :ref:`SpecTypeSpecificationItemType`

.. _SpecTypeGlossaryItemType:

Glossary Item Type
==================

This type refines the :ref:`SpecTypeRootItemType` through the ``type``
attribute if the value is ``glossary``. This set of attributes specifies a
glossary item. All explicit attributes shall be specified. The explicit
attributes for this type are:

glossary-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    glossary item type.

This type is refined by the following types:

- :ref:`SpecTypeGlossaryGroupItemType`

- :ref:`SpecTypeGlossaryTermItemType`

.. _SpecTypeGlossaryGroupItemType:

Glossary Group Item Type
========================

This type refines the :ref:`SpecTypeGlossaryItemType` through the
``glossary-type`` attribute if the value is ``group``. This set of attributes
specifies a glossary group. All explicit attributes shall be specified. The
explicit attributes for this type are:

name
    The attribute value shall be a string. It shall be the human readable name
    of the glossary group.

text
    The attribute value shall be a string. It shall state the requirement for
    the glossary group.

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

.. _SpecTypeProxyItemType:

Proxy Item Type
===============

This type refines the :ref:`SpecTypeRootItemType` through the ``type``
attribute if the value is ``proxy``. Items of similar characteristics may link
to a proxy item through links with the :ref:`SpecTypeProxyMemberLinkRole`.  A
proxy item resolves to the first member item which is enabled.  Proxies may be
used to provide an interface with a common name and implementations which
depend on configuration options.  For example, in one configuration a constant
could be a compile time constant and in another configuration it could be a
read-only object.

.. _SpecTypeReference:

Reference
=========

This type refines the :ref:`SpecTypeRootItemType` through the ``type``
attribute if the value is ``reference``. This set of attributes specifies a
reference to something with a title. All explicit attributes shall be
specified. The explicit attributes for this type are:

reference-type
    The attribute value shall be a string. It shall be the reference type.

title
    The attribute value shall be a string. It shall be the title of the work.

work-hash
    The attribute value shall be an :ref:`SpecTypeOptionalSHA256Digest`. If the
    value is present, then it shall be the SHA256 hash value of the referenced
    work.

work-url
    The attribute value shall be an optional string. If the value is present,
    then it shall be the URL to the referenced work.

This type is refined by the following types:

- :ref:`SpecTypeArticleReference`

- :ref:`SpecTypeBookReference`

- :ref:`SpecTypeBookletReference`

- :ref:`SpecTypeConferenceProceedingsReference`

- :ref:`SpecTypeInBookReference`

- :ref:`SpecTypeInCollectionReference`

- :ref:`SpecTypeInConferenceProceedingsReference`

- :ref:`SpecTypeManualReference`

- :ref:`SpecTypeMastersOrPhDThesisReference`

- :ref:`SpecTypeMiscellaneousReference`

- :ref:`SpecTypeTechnicalReportReference`

.. _SpecTypeArticleReference:

Article Reference
=================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``article``. This set of attributes specifies a
reference to an article. The following explicit attributes are mandatory:

- ``author``

- ``journal``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the article.

doi
    The attribute value shall be a string. It shall be the digital object
    identifier (DOI) of the article.

journal
    The attribute value shall be a string. It shall be the name of the journal,
    magazine, report, or newspaper in which the article was published.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    journal, magazine, or report.

pages
    The attribute value shall be a string. It shall be the page numbers on
    which the article appears.

volume
    The attribute value shall be a string. It shall be the volume number of the
    journal.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeBookReference:

Book Reference
==============

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``book``. This set of attributes specifies a
reference to a book. The following explicit attributes are mandatory:

- ``author``

- ``publisher``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the book.

edition
    The attribute value shall be a string. It shall be the edition of the book.

editor
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the editor or the list of editors of the book.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    book.

publisher
    The attribute value shall be a string. It shall be the name of the
    publisher.

series
    The attribute value shall be a string. It shall be the series of books the
    book was published.

volume
    The attribute value shall be a string. It shall be the volume of a
    multi-volume book.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeBookletReference:

Booklet Reference
=================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``booklet``. This set of attributes specifies a
reference to a booklet. None of the explicit attributes is mandatory, they are
all optional. The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the booklet.

howpublished
    The attribute value shall be a string. It shall be the publishing method.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeConferenceProceedingsReference:

Conference Proceedings Reference
================================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``proceedings``. This set of attributes specifies a
reference to the proceedings of a conference. Only the ``year`` attribute is
mandatory. The explicit attributes for this type are:

editor
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the editor or the list of editors of the conference proceedings.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    conference proceedings.

organization
    The attribute value shall be a string. It shall be the associated
    organization.

publisher
    The attribute value shall be a string. It shall be the name of the
    publisher.

series
    The attribute value shall be a string. It shall be the series of the
    conference proceedings the article was published.

volume
    The attribute value shall be a string. It shall be the volume of the
    conference proceedings.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeInBookReference:

In Book Reference
=================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``inbook``. This set of attributes specifies a
reference to a work in a book. The following explicit attributes are mandatory:

- ``author``

- ``chapter``

- ``pages``

- ``publisher``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the book.

chapter
    The attribute value shall be a string. It shall be the chapter number.

edition
    The attribute value shall be a string. It shall be the edition of the book.

editor
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the editor or the list of editors of the book.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    journal, magazine, or tech-report.

pages
    The attribute value shall be a string. It shall be the page numbers,
    separated either by commas or double-hyphens.

publication-type
    The attribute value shall be a string. If the attribute is present, it
    shall be the publication type overriding the default.

publisher
    The attribute value shall be a string. It shall be the name of the
    publisher.

series
    The attribute value shall be a string. It shall be the series of books the
    book was published.

volume
    The attribute value shall be a string. It shall be the volume of a
    multi-volume book.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeInCollectionReference:

In Collection Reference
=======================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``incollection``. This set of attributes specifies a
reference to a work in a book. The following explicit attributes are mandatory:

- ``author``

- ``booktitle``

- ``publisher``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the book.

booktitle
    The attribute value shall be a string. It shall be the title of the book.

chapter
    The attribute value shall be a string. It shall be the chapter number.

edition
    The attribute value shall be a string. It shall be the edition of the book.

editor
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the editor or the list of editors of the book.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    journal, magazine, or tech-report.

pages
    The attribute value shall be a string. It shall be the page numbers,
    separated either by commas or double-hyphens.

publication-type
    The attribute value shall be a string. If the attribute is present, it
    shall be the publication type overriding the default.

publisher
    The attribute value shall be a string. It shall be the name of the
    publisher.

series
    The attribute value shall be a string. It shall be the series of books the
    book was published.

volume
    The attribute value shall be a string. It shall be the volume of a
    multi-volume book.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeInConferenceProceedingsReference:

In Conference Proceedings Reference
===================================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``inproceedings``. This set of attributes specifies a
reference to an article in a conference proceedings. The following explicit
attributes are mandatory:

- ``author``

- ``booktitle``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the article.

booktitle
    The attribute value shall be a string. It shall be the title of the
    conference proceedings.

doi
    The attribute value shall be a string. It shall be the digital object
    identifier (DOI) of the article.

editor
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the editor or the list of editors of the article.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    conference proceedings.

organization
    The attribute value shall be a string. It shall be the associated
    organization.

pages
    The attribute value shall be a string. It shall be the page numbers,
    separated either by commas or double-hyphens.

publisher
    The attribute value shall be a string. It shall be the name of the
    publisher.

series
    The attribute value shall be a string. It shall be the series of the
    conference proceedings the article was published.

volume
    The attribute value shall be a string. It shall be the volume of the
    conference proceedings.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeManualReference:

Manual Reference
================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``manual``. This set of attributes specifies a
reference to a manual. None of the explicit attributes is mandatory, they are
all optional. The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the manual.

edition
    The attribute value shall be a string. It shall be the edition of the
    manual.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

organization
    The attribute value shall be a string. It shall be the associated
    organization.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeMastersOrPhDThesisReference:

Masters or Ph.D. Thesis Reference
=================================

This type refines the following types:

- :ref:`SpecTypeReference` through the ``reference-type`` attribute if the
  value is ``mastersthesis``

- :ref:`SpecTypeReference` through the ``reference-type`` attribute if the
  value is ``phdthesis``

This set of attributes specifies a reference to a masters or Ph.D. thesis. The
following explicit attributes are mandatory:

- ``author``

- ``school``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the thesis.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

publication-type
    The attribute value shall be a string. If the attribute is present, it
    shall be the publication type overriding the default.

school
    The attribute value shall be a string. It shall be the school where the
    thesis was written.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeMiscellaneousReference:

Miscellaneous Reference
=======================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``misc``. This set of attributes specifies a
reference to a work. None of the explicit attributes is mandatory, they are all
optional. The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the work.

howpublished
    The attribute value shall be a string. It shall be the publishing method.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeTechnicalReportReference:

Technical Report Reference
==========================

This type refines the :ref:`SpecTypeReference` through the ``reference-type``
attribute if the value is ``techreport``. This set of attributes specifies a
reference to a technical report. The following explicit attributes are
mandatory:

- ``author``

- ``institution``

- ``year``

The explicit attributes for this type are:

author
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. It shall
    be the author or the list of authors of the technical report.

institution
    The attribute value shall be a string. It shall be the institution that was
    involved in the publishing.

month
    The attribute value shall be a :ref:`SpecTypeMonth`. It shall be the month
    of publication.

note
    The attribute value shall be a string. It shall be associated miscellaneous
    information.

number
    The attribute value shall be a string. It shall be the issue number of the
    technical report.

publication-type
    The attribute value shall be a string. If the attribute is present, it
    shall be the publication type overriding the default.

year
    The attribute value shall be a string. It shall be the year of publication.

.. _SpecTypeSpecificationItemType:

Specification Item Type
=======================

This type refines the :ref:`SpecTypeRootItemType` through the ``type``
attribute if the value is ``spec``. This set of attributes specifies
specification types. All explicit attributes shall be specified. The explicit
attributes for this type are:

spec-description
    The attribute value shall be an optional string. It shall be the
    description of the specification type.

spec-example
    The attribute value shall be an optional string. If the value is present,
    then it shall be an example of the specification type.

spec-info
    The attribute value shall be a :ref:`SpecTypeSpecificationInformation`.

spec-name
    The attribute value shall be an optional string. It shall be the human
    readable name of the specification type.

spec-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall the
    specification type.

Please have a look at the following example:

.. code-block:: yaml

    SPDX-License-Identifier: CC-BY-SA-4.0 OR BSD-2-Clause
    copyrights:
    - Copyright (C) 2020 embedded brains GmbH & Co. KG
    enabled-by: true
    links:
    - role: spec-member
      uid: root
    - role: spec-refinement
      spec-key: type
      spec-value: example
      uid: root
    spec-description: null
    spec-example: null
    spec-info:
      dict:
        attributes:
          an-example-attribute:
            description: |
              It shall be an example.
            spec-type: optional-str
          example-number:
            description: |
              It shall be the example number.
            spec-type: int
        description: |
          This set of attributes specifies an example.
        mandatory-attributes: all
    spec-name: Example Item Type
    spec-type: spec
    type: spec

.. _SpecificationAttributeSetsAndValueTypes:

Specification attribute sets and value types
********************************************

.. _SpecTypeCitationGroupMemberLinkRole:

Citation Group Member Link Role
===============================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``citation-group-member``. This set of attributes specifies a citation
group membership role of links.  A group citation lists citations for all group
members with the associated group key. All explicit attributes shall be
specified. The explicit attributes for this type are:

citation-group-key
    The attribute value shall be a string. It shall be the citation group key.

.. _SpecTypeCopyright:

Copyright
=========

The value shall be a string. It shall be a copyright statement of a copyright
holder of the specification item. The value

- shall match with the regular expression
  "``^\s*Copyright\s+\(C\)\s+[0-9]+,\s*[0-9]+\s+.+\s*$``",

- or, shall match with the regular expression
  "``^\s*Copyright\s+\(C\)\s+[0-9]+\s+.+\s*$``",

- or, shall match with the regular expression
  "``^\s*Copyright\s+\(C\)\s+.+\s*$``".

This type is used by the following types:

- :ref:`SpecTypeRootItemType`

.. _SpecTypeEnabledSetAction:

Enabled Set Action
==================

This set of attributes specifies an action to alter the enabled set. All
explicit attributes shall be specified. The explicit attributes for this type
are:

action
    The attribute value shall be an :ref:`SpecTypeEnabledSetActions`. It shall
    be the enabled set action.

enabled-by
    The attribute value shall be an :ref:`SpecTypeEnabledByExpression`. It
    shall define the conditions under which the action is enabled.

value
    The attribute value shall be a :ref:`SpecTypeStringOrStringList`. If shall
    be the action value.

.. _SpecTypeEnabledSetActions:

Enabled Set Actions
===================

The value shall be a string. It specifies the enabled set actions. The value
shall be an element of

- "``add``",

- "``remove``", and

- "``set``".

This type is used by the following types:

- :ref:`SpecTypeEnabledSetAction`

.. _SpecTypeEnabledByExpression:

Enabled-By Expression
=====================

A value of this type shall be an expression which defines under which
conditions the specification item or parts of it are enabled.  The expression
is evaluated with the use of an *enabled set*.  This is a set of strings which
indicate enabled features.

A value of this type shall be of one of the following variants:

- The value may be a boolean. This expression evaluates directly to the boolean
  value.

- The value may be a set of attributes. Each attribute defines an operator.
  Exactly one of the explicit attributes shall be specified. The explicit
  attributes for this type are:

  and
      The attribute value shall be a list. Each list element shall be an
      :ref:`SpecTypeEnabledByExpression`. The **and** operator evaluates to the
      **logical and** of the evaluation results of the expressions in the list.

  eq
      The attribute value shall be a list of strings. The **eq** operator
      evaluates a list of strings with at least one element.  If all strings
      are equal, then the evaluation result is true, otherwise false.

  not
      The attribute value shall be an :ref:`SpecTypeEnabledByExpression`. The
      **not** operator evaluates to the **logical not** of the evaluation
      results of the expression.

  or
      The attribute value shall be a list. Each list element shall be an
      :ref:`SpecTypeEnabledByExpression`. The **or** operator evaluates to the
      **logical or** of the evaluation results of the expressions in the list.

- The value may be a list. Each list element shall be an
  :ref:`SpecTypeEnabledByExpression`. This list of expressions evaluates to the
  **logical or** of the evaluation results of the expressions in the list.

- The value may be a string. If the value is in the *enabled set*, this
  expression evaluates to true, otherwise to false.

This type is used by the following types:

- :ref:`SpecTypeEnabledByExpression`

- :ref:`SpecTypeEnabledSetAction`

- :ref:`SpecTypeRootItemType`

Please have a look at the following example:

.. code-block:: yaml

    enabled-by:
      and:
      - SOME_FEATURE
      - not: ANOTHER_FEATURE

.. _SpecTypeGlossaryLinkRole:

Glossary Link Role
==================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``glossary``. Items may link to a glossary group using this role.

.. _SpecTypeGlossaryMembershipLinkRole:

Glossary Membership Link Role
=============================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``glossary-member``. It defines the glossary membership role of links.

.. _SpecTypeGlossaryRefinementLinkRole:

Glossary Refinement Link Role
=============================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``glossary-refinement``. It defines the glossary refinement role of
links.

.. _SpecTypeIntegerOrString:

Integer or String
=================

A value of this type shall be of one of the following variants:

- The value may be an integer number.

- The value may be a string.

.. _SpecTypeLink:

Link
====

This set of attributes specifies a link from one specification item to another
specification item.  The links in a list are ordered.  The first link in the
list is processed first. All explicit attributes shall be specified. The
explicit attributes for this type are:

role
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the role of
    the link.

uid
    The attribute value shall be an :ref:`SpecTypeUID`. It shall be the
    absolute or relative UID of the link target item.

This type is refined by the following types:

- :ref:`SpecTypeCitationGroupMemberLinkRole`

- :ref:`SpecTypeGlossaryLinkRole`

- :ref:`SpecTypeGlossaryMembershipLinkRole`

- :ref:`SpecTypeGlossaryRefinementLinkRole`

- :ref:`SpecTypeProxyMemberLinkRole`

- :ref:`SpecTypeSpecificationMemberLinkRole`

- :ref:`SpecTypeSpecificationRefinementLinkRole`

This type is used by the following types:

- :ref:`SpecTypeRootItemType`

.. _SpecTypeMD5Digest:

MD5 Digest
==========

The value shall be a string. It shall be a MD5 digest encoded in base64url. The
value shall match with the regular expression "``^[A-Za-z0-9+_=-]{24}$``".

.. _SpecTypeMD5HexDigest:

MD5 Hex Digest
==============

The value shall be a string. It shall be a MD5 digest encoded in hexadecimal
digits. The value shall match with the regular expression
"``^[A-Fa-f0-9]{32}$``".

.. _SpecTypeMonth:

Month
=====

The value shall be a string. It specifies a month. The value shall be an
element of

- "``January``",

- "``February``",

- "``March``",

- "``April``",

- "``May``",

- "``June``",

- "``July``",

- "``August``",

- "``September``",

- "``October``",

- "``November``", and

- "``December``".

This type is used by the following types:

- :ref:`SpecTypeArticleReference`

- :ref:`SpecTypeBookReference`

- :ref:`SpecTypeBookletReference`

- :ref:`SpecTypeConferenceProceedingsReference`

- :ref:`SpecTypeInBookReference`

- :ref:`SpecTypeInCollectionReference`

- :ref:`SpecTypeInConferenceProceedingsReference`

- :ref:`SpecTypeManualReference`

- :ref:`SpecTypeMastersOrPhDThesisReference`

- :ref:`SpecTypeMiscellaneousReference`

- :ref:`SpecTypeTechnicalReportReference`

.. _SpecTypeName:

Name
====

The value shall be a string. It shall be an attribute name. The value shall
match with the regular expression
"``^([a-z][a-z0-9-]*|SPDX-License-Identifier)$``".

This type is used by the following types:

- :ref:`SpecTypeGlossaryItemType`

- :ref:`SpecTypeLink`

- :ref:`SpecTypeRootItemType`

- :ref:`SpecTypeSpecificationAttributeValue`

- :ref:`SpecTypeSpecificationExplicitAttributes`

- :ref:`SpecTypeSpecificationGenericAttributes`

- :ref:`SpecTypeSpecificationItemType`

- :ref:`SpecTypeSpecificationList`

- :ref:`SpecTypeSpecificationRefinementLinkRole`

.. _SpecTypeOptionalFloatingPointNumber:

Optional Floating-Point Number
==============================

A value of this type shall be of one of the following variants:

- The value may be a floating-point number.

- There may be no value (null).

.. _SpecTypeOptionalInteger:

Optional Integer
================

A value of this type shall be of one of the following variants:

- The value may be an integer number.

- There may be no value (null).

This type is used by the following types:

- :ref:`SpecTypeSubprocessAction`

.. _SpecTypeOptionalIntegerOrString:

Optional Integer or String
==========================

A value of this type shall be of one of the following variants:

- The value may be an integer number.

- There may be no value (null).

- The value may be a string.

.. _SpecTypeOptionalIntegerOrStringList:

Optional Integer or String List
===============================

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be an
  :ref:`SpecTypeIntegerOrString`.

- There may be no value (null).

.. _SpecTypeOptionalListOfStringLists:

Optional List of String Lists
=============================

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be a list of strings.

- There may be no value (null).

.. _SpecTypeOptionalMD5Digest:

Optional MD5 Digest
===================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. If the value is present, then it shall be a MD5
  digest encoded in base64url. The value shall match with the regular
  expression "``^[A-Za-z0-9+_=-]{24}$``".

.. _SpecTypeOptionalMD5HexDigest:

Optional MD5 Hex Digest
=======================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. If the value is present, then it shall be a MD5
  digest encoded in hexadecimal digits. The value shall match with the regular
  expression "``^[A-Fa-f0-9]{32}$``".

.. _SpecTypeOptionalSHA256Digest:

Optional SHA256 Digest
======================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. It shall be a SHA256 digest encoded in base64url.
  The value shall match with the regular expression "``^[A-Za-z0-9+_=-]{44}$``".

This type is used by the following types:

- :ref:`SpecTypeReference`

.. _SpecTypeOptionalSHA256HexDigest:

Optional SHA256 Hex Digest
==========================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. It shall be a SHA256 digest encoded in hexadecimal
  digits. The value shall match with the regular expression
  "``^[A-Fa-f0-9]{64}$``".

.. _SpecTypeOptionalSHA512Digest:

Optional SHA512 Digest
======================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. If the value is present, then it shall be a SHA512
  digest encoded in base64url. The value shall match with the regular
  expression "``^[A-Za-z0-9+_=-]{88}$``".

.. _SpecTypeOptionalSHA512HexDigest:

Optional SHA512 Hex Digest
==========================

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string. If the value is present, then it shall be a SHA512
  digest encoded in hexadecimal digits. The value shall match with the regular
  expression "``^[A-Fa-f0-9]{128}$``".

.. _SpecTypeOptionalString:

Optional String
===============

A value of this type shall be of one of the following variants:

- There may be no value (null).

- The value may be a string.

.. _SpecTypeOptionalStringList:

Optional String List
====================

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be a string.

- There may be no value (null).

.. _SpecTypeOptionalStringOrStringList:

Optional String or String List
==============================

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be a string.

- There may be no value (null).

- The value may be a string.

.. _SpecTypeProxyMemberLinkRole:

Proxy Member Link Role
======================

This type refines the following types:

- :ref:`SpecTypeLink` through the ``role`` attribute if the value is
  ``proxy-member``

- :ref:`SpecTypeLink` through the ``role`` attribute if the value is
  ``proxy-member-default``

It defines the proxy member role of links.  Items may use this role to link to
:ref:`SpecTypeProxyItemType` items.

.. _SpecTypeSHA256Digest:

SHA256 Digest
=============

The value shall be a string. It shall be a SHA256 digest encoded in base64url.
The value shall match with the regular expression "``^[A-Za-z0-9+_=-]{44}$``".

.. _SpecTypeSHA256HexDigest:

SHA256 Hex Digest
=================

The value shall be a string. It shall be a SHA256 digest encoded in hexadecimal
digits. The value shall match with the regular expression
"``^[A-Fa-f0-9]{64}$``".

.. _SpecTypeSHA512Digest:

SHA512 Digest
=============

The value shall be a string. It shall be a SHA512 digest encoded in base64url.
The value shall match with the regular expression "``^[A-Za-z0-9+_=-]{88}$``".

.. _SpecTypeSHA512HexDigest:

SHA512 Hex Digest
=================

The value shall be a string. It shall be a SHA512 digest encoded in hexadecimal
digits. The value shall match with the regular expression
"``^[A-Fa-f0-9]{128}$``".

.. _SpecTypeSPDXLicenseIdentifier:

SPDX License Identifier
=======================

The value shall be a string. It defines the license of the item expressed
though an SPDX License Identifier. The value

- shall be equal to "``CC-BY-SA-4.0``",

- or, shall be equal to "``CC-BY-SA-4.0 OR BSD-2-Clause``",

- or, shall be equal to "``CC-BY-SA-4.0 OR BSD-2-Clause OR MIT``",

- or, shall be equal to "``CC-BY-SA-4.0 OR MIT``",

- or, shall be equal to "``BSD-2-Clause``",

- or, shall be equal to "``BSD-2-Clause OR MIT``",

- or, shall be equal to "``ECSS``",

- or, shall be equal to "``ESA UNCLASSIFIED - For Official Use``",

- or, shall be equal to "``MIT``".

This type is used by the following types:

- :ref:`SpecTypeRootItemType`

.. _SpecTypeSpecificationAttributeSet:

Specification Attribute Set
===========================

This set of attributes specifies a set of attributes. The following explicit
attributes are mandatory:

- ``attributes``

- ``description``

- ``mandatory-attributes``

The explicit attributes for this type are:

attributes
    The attribute value shall be a
    :ref:`SpecTypeSpecificationExplicitAttributes`. It shall specify the
    explicit attributes of the attribute set.

description
    The attribute value shall be an optional string. It shall be the
    description of the attribute set.

generic-attributes
    The attribute value shall be a
    :ref:`SpecTypeSpecificationGenericAttributes`. It shall specify the generic
    attributes of the attribute set.

mandatory-attributes
    The attribute value shall be a
    :ref:`SpecTypeSpecificationMandatoryAttributes`. It shall specify the
    mandatory attributes of the attribute set.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeSpecificationAttributeValue:

Specification Attribute Value
=============================

This set of attributes specifies an attribute value. All explicit attributes
shall be specified. The explicit attributes for this type are:

description
    The attribute value shall be an optional string. It shall be the
    description of the attribute value.

spec-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type of the attribute value.

This type is used by the following types:

- :ref:`SpecTypeSpecificationExplicitAttributes`

.. _SpecTypeSpecificationBooleanValue:

Specification Boolean Value
===========================

This attribute set specifies a boolean value. Only the ``description``
attribute is mandatory. The explicit attributes for this type are:

assert
    The attribute value shall be a boolean. This optional attribute defines the
    value constraint of the specified boolean value.  If the value of the
    assert attribute is true, then the value of the specified boolean value
    shall be true.  If the value of the assert attribute is false, then the
    value of the specified boolean value shall be false.  In case the assert
    attribute is not present, then the value of the specified boolean value may
    be true or false.

description
    The attribute value shall be an optional string. It shall be the
    description of the specified boolean value.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeSpecificationExplicitAttributes:

Specification Explicit Attributes
=================================

Generic attributes may be specified. Each generic attribute key shall be a
:ref:`SpecTypeName`. Each generic attribute value shall be a
:ref:`SpecTypeSpecificationAttributeValue`. Each generic attribute specifies an
explicit attribute of the attribute set.  The key of the each generic attribute
defines the attribute key of the explicit attribute.

This type is used by the following types:

- :ref:`SpecTypeSpecificationAttributeSet`

.. _SpecTypeSpecificationFloatingPointAssert:

Specification Floating-Point Assert
===================================

A value of this type shall be an expression which asserts that the
floating-point value of the specified attribute satisfies the required
constraints.

A value of this type shall be of one of the following variants:

- The value may be a set of attributes. Each attribute defines an operator.
  Exactly one of the explicit attributes shall be specified. The explicit
  attributes for this type are:

  and
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationFloatingPointAssert`. The **and** operator
      evaluates to the **logical and** of the evaluation results of the
      expressions in the list.

  eq
      The attribute value shall be a floating-point number. The **eq** operator
      evaluates to true, if the value to check is equal to the value of this
      attribute, otherwise to false.

  ge
      The attribute value shall be a floating-point number. The **ge** operator
      evaluates to true, if the value to check is greater than or equal to the
      value of this attribute, otherwise to false.

  gt
      The attribute value shall be a floating-point number. The **gt** operator
      evaluates to true, if the value to check is greater than the value of
      this attribute, otherwise to false.

  le
      The attribute value shall be a floating-point number. The **le** operator
      evaluates to true, if the value to check is less than or equal to the
      value of this attribute, otherwise to false.

  lt
      The attribute value shall be a floating-point number. The **lt** operator
      evaluates to true, if the value to check is less than the value of this
      attribute, otherwise to false.

  ne
      The attribute value shall be a floating-point number. The **ne** operator
      evaluates to true, if the value to check is not equal to the value of
      this attribute, otherwise to false.

  not
      The attribute value shall be a
      :ref:`SpecTypeSpecificationFloatingPointAssert`. The **not** operator
      evaluates to the **logical not** of the evaluation results of the
      expression.

  or
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationFloatingPointAssert`. The **or** operator
      evaluates to the **logical or** of the evaluation results of the
      expressions in the list.

- The value may be a list. Each list element shall be a
  :ref:`SpecTypeSpecificationFloatingPointAssert`. This list of expressions
  evaluates to the **logical or** of the evaluation results of the expressions
  in the list.

This type is used by the following types:

- :ref:`SpecTypeSpecificationFloatingPointAssert`

- :ref:`SpecTypeSpecificationFloatingPointValue`

.. _SpecTypeSpecificationFloatingPointValue:

Specification Floating-Point Value
==================================

This set of attributes specifies a floating-point value. Only the
``description`` attribute is mandatory. The explicit attributes for this type
are:

assert
    The attribute value shall be a
    :ref:`SpecTypeSpecificationFloatingPointAssert`. This optional attribute
    defines the value constraints of the specified floating-point value.  In
    case the assert attribute is not present, then the value of the specified
    floating-point value may be every valid floating-point number.

description
    The attribute value shall be an optional string. It shall be the
    description of the specified floating-point value.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeSpecificationGenericAttributes:

Specification Generic Attributes
================================

This set of attributes specifies generic attributes.  Generic attributes are
attributes which are not explicitly specified by
:ref:`SpecTypeSpecificationExplicitAttributes`.  They are restricted to uniform
attribute key and value types. All explicit attributes shall be specified. The
explicit attributes for this type are:

description
    The attribute value shall be an optional string. It shall be the
    description of the generic attributes.

key-spec-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type of the generic attribute keys.

value-spec-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type of the generic attribute values.

This type is used by the following types:

- :ref:`SpecTypeSpecificationAttributeSet`

.. _SpecTypeSpecificationInformation:

Specification Information
=========================

This set of attributes specifies attribute values. At least one of the explicit
attributes shall be specified. The explicit attributes for this type are:

bool
    The attribute value shall be a :ref:`SpecTypeSpecificationBooleanValue`. It
    shall specify a boolean value.

dict
    The attribute value shall be a :ref:`SpecTypeSpecificationAttributeSet`. It
    shall specify a set of attributes.

float
    The attribute value shall be a
    :ref:`SpecTypeSpecificationFloatingPointValue`. It shall specify a
    floating-point value.

int
    The attribute value shall be a :ref:`SpecTypeSpecificationIntegerValue`. It
    shall specify an integer value.

list
    The attribute value shall be a :ref:`SpecTypeSpecificationList`. It shall
    specify a list of attributes or values.

none
    The attribute shall have no value. It specifies that no value is required.

str
    The attribute value shall be a :ref:`SpecTypeSpecificationStringValue`. It
    shall specify a string.

This type is used by the following types:

- :ref:`SpecTypeSpecificationItemType`

.. _SpecTypeSpecificationIntegerAssert:

Specification Integer Assert
============================

A value of this type shall be an expression which asserts that the integer
value of the specified attribute satisfies the required constraints.

A value of this type shall be of one of the following variants:

- The value may be a set of attributes. Each attribute defines an operator.
  Exactly one of the explicit attributes shall be specified. The explicit
  attributes for this type are:

  and
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationIntegerAssert`. The **and** operator evaluates
      to the **logical and** of the evaluation results of the expressions in
      the list.

  eq
      The attribute value shall be an integer number. The **eq** operator
      evaluates to true, if the value to check is equal to the value of this
      attribute, otherwise to false.

  ge
      The attribute value shall be an integer number. The **ge** operator
      evaluates to true, if the value to check is greater than or equal to the
      value of this attribute, otherwise to false.

  gt
      The attribute value shall be an integer number. The **gt** operator
      evaluates to true, if the value to check is greater than the value of
      this attribute, otherwise to false.

  le
      The attribute value shall be an integer number. The **le** operator
      evaluates to true, if the value to check is less than or equal to the
      value of this attribute, otherwise to false.

  lt
      The attribute value shall be an integer number. The **lt** operator
      evaluates to true, if the value to check is less than the value of this
      attribute, otherwise to false.

  ne
      The attribute value shall be an integer number. The **ne** operator
      evaluates to true, if the value to check is not equal to the value of
      this attribute, otherwise to false.

  not
      The attribute value shall be a :ref:`SpecTypeSpecificationIntegerAssert`.
      The **not** operator evaluates to the **logical not** of the evaluation
      results of the expression.

  or
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationIntegerAssert`. The **or** operator evaluates
      to the **logical or** of the evaluation results of the expressions in the
      list.

- The value may be a list. Each list element shall be a
  :ref:`SpecTypeSpecificationIntegerAssert`. This list of expressions evaluates
  to the **logical or** of the evaluation results of the expressions in the
  list.

This type is used by the following types:

- :ref:`SpecTypeSpecificationIntegerAssert`

- :ref:`SpecTypeSpecificationIntegerValue`

.. _SpecTypeSpecificationIntegerValue:

Specification Integer Value
===========================

This set of attributes specifies an integer value. Only the ``description``
attribute is mandatory. The explicit attributes for this type are:

assert
    The attribute value shall be a :ref:`SpecTypeSpecificationIntegerAssert`.
    This optional attribute defines the value constraints of the specified
    integer value.  In case the assert attribute is not present, then the value
    of the specified integer value may be every valid integer number.

description
    The attribute value shall be an optional string. It shall be the
    description of the specified integer value.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeSpecificationList:

Specification List
==================

This set of attributes specifies a list of attributes or values. All explicit
attributes shall be specified. The explicit attributes for this type are:

description
    The attribute value shall be an optional string. It shall be the
    description of the list.

spec-type
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type of elements of the list.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeSpecificationMandatoryAttributes:

Specification Mandatory Attributes
==================================

It defines which explicit attributes are mandatory.

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be a :ref:`SpecTypeName`.
  The list defines the mandatory attributes through their key names.

- The value may be a string. It defines how many explicit attributes are
  mandatory.  If ``none`` is used, then none of the explicit attributes is
  mandatory, they are all optional. The value shall be an element of

  - "``all``",

  - "``at-least-one``",

  - "``at-most-one``",

  - "``exactly-one``", and

  - "``none``".

This type is used by the following types:

- :ref:`SpecTypeSpecificationAttributeSet`

.. _SpecTypeSpecificationMemberLinkRole:

Specification Member Link Role
==============================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``spec-member``. It defines the specification membership role of
links.

.. _SpecTypeSpecificationRefinementLinkRole:

Specification Refinement Link Role
==================================

This type refines the :ref:`SpecTypeLink` through the ``role`` attribute if the
value is ``spec-refinement``. It defines the specification refinement role of
links. All explicit attributes shall be specified. The explicit attributes for
this type are:

spec-key
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type refinement attribute key of the specification
    refinement.

spec-value
    The attribute value shall be a :ref:`SpecTypeName`. It shall be the
    specification type refinement attribute value of the specification
    refinement.

.. _SpecTypeSpecificationStringAssert:

Specification String Assert
===========================

A value of this type shall be an expression which asserts that the string of
the specified attribute satisfies the required constraints.

A value of this type shall be of one of the following variants:

- The value may be a set of attributes. Each attribute defines an operator.
  Exactly one of the explicit attributes shall be specified. The explicit
  attributes for this type are:

  and
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationStringAssert`. The **and** operator evaluates
      to the **logical and** of the evaluation results of the expressions in
      the list.

  contains
      The attribute value shall be a list of strings. The **contains** operator
      evaluates to true, if the string to check converted to lower case with
      all white space characters converted to a single space character contains
      a string of the list of strings of this attribute, otherwise to false.

  eq
      The attribute value shall be a string. The **eq** operator evaluates to
      true, if the string to check is equal to the value of this attribute,
      otherwise to false.

  ge
      The attribute value shall be a string. The **ge** operator evaluates to
      true, if the string to check is greater than or equal to the value of
      this attribute, otherwise to false.

  gt
      The attribute value shall be a string. The **gt** operator evaluates to
      true, if the string to check is greater than the value of this attribute,
      otherwise to false.

  in
      The attribute value shall be a list of strings. The **in** operator
      evaluates to true, if the string to check is contained in the list of
      strings of this attribute, otherwise to false.

  le
      The attribute value shall be a string. The **le** operator evaluates to
      true, if the string to check is less than or equal to the value of this
      attribute, otherwise to false.

  lt
      The attribute value shall be a string. The **lt** operator evaluates to
      true, if the string to check is less than the value of this attribute,
      otherwise to false.

  ne
      The attribute value shall be a string. The **ne** operator evaluates to
      true, if the string to check is not equal to the value of this attribute,
      otherwise to false.

  not
      The attribute value shall be a :ref:`SpecTypeSpecificationStringAssert`.
      The **not** operator evaluates to the **logical not** of the evaluation
      results of the expression.

  or
      The attribute value shall be a list. Each list element shall be a
      :ref:`SpecTypeSpecificationStringAssert`. The **or** operator evaluates
      to the **logical or** of the evaluation results of the expressions in the
      list.

  re
      The attribute value shall be a string. The **re** operator evaluates to
      true, if the string to check matches with the regular expression of this
      attribute, otherwise to false.

  uid
      The attribute shall have no value. The **uid** operator evaluates to
      true, if the string is a valid UID, otherwise to false.

- The value may be a list. Each list element shall be a
  :ref:`SpecTypeSpecificationStringAssert`. This list of expressions evaluates
  to the **logical or** of the evaluation results of the expressions in the
  list.

This type is used by the following types:

- :ref:`SpecTypeSpecificationStringAssert`

- :ref:`SpecTypeSpecificationStringValue`

.. _SpecTypeSpecificationStringValue:

Specification String Value
==========================

This set of attributes specifies a string. Only the ``description`` attribute
is mandatory. The explicit attributes for this type are:

assert
    The attribute value shall be a :ref:`SpecTypeSpecificationStringAssert`.
    This optional attribute defines the constraints of the specified string.
    In case the assert attribute is not present, then the specified string may
    be every valid string.

description
    The attribute value shall be an optional string. It shall be the
    description of the specified string attribute.

This type is used by the following types:

- :ref:`SpecTypeSpecificationInformation`

.. _SpecTypeStringOrStringList:

String or String List
=====================

A value of this type shall be of one of the following variants:

- The value may be a list. Each list element shall be a string.

- The value may be a string.

This type is used by the following types:

- :ref:`SpecTypeArticleReference`

- :ref:`SpecTypeBookReference`

- :ref:`SpecTypeBookletReference`

- :ref:`SpecTypeConferenceProceedingsReference`

- :ref:`SpecTypeEnabledSetAction`

- :ref:`SpecTypeInBookReference`

- :ref:`SpecTypeInCollectionReference`

- :ref:`SpecTypeInConferenceProceedingsReference`

- :ref:`SpecTypeManualReference`

- :ref:`SpecTypeMastersOrPhDThesisReference`

- :ref:`SpecTypeMiscellaneousReference`

- :ref:`SpecTypeStringToStringOrListOfStringsMapping`

- :ref:`SpecTypeTechnicalReportReference`

.. _SpecTypeStringToStringMapping:

String to String Mapping
========================

This set of attributes specifies a mapping from one string to another string.
Generic attributes may be specified. Each generic attribute key shall be a
string. Each generic attribute value shall be a string.

.. _SpecTypeStringToStringOrListOfStringsMapping:

String to String or List of Strings Mapping
===========================================

This set of attributes specifies a mapping from one string to another string or
a list of strings. Generic attributes may be specified. Each generic attribute
key shall be a string. Each generic attribute value shall be a
:ref:`SpecTypeStringOrStringList`.

.. _SpecTypeSubprocessAction:

Subprocess Action
=================

This set of attributes specifies a subprocess to run. The following explicit
attributes are mandatory:

- ``command``

- ``env``

- ``expected-return-code``

- ``working-directory``

The explicit attributes for this type are:

command
    The attribute value shall be a list of strings. It shall be the command and
    argument list to run as a subprocess.  A variable substitution is performed
    on the list elements.  For example, you can use ``${.:/input-file}.bin`` or
    `${.:/output-file}`.

env
    The attribute value shall be a list. Each list element shall be a
    :ref:`SpecTypeSubprocessEnvironmentAction`.

expected-return-code
    The attribute value shall be an :ref:`SpecTypeOptionalInteger`. If the
    value is present, then it shall be the expected return code of the
    subprocess.

stdout
    The attribute value shall be an optional string. It the value is present,
    then it shall be the target file of the standard output stream.

working-directory
    The attribute value shall be a string. It shall be the working directory of
    the subprocess.

.. _SpecTypeSubprocessEnvironmentAction:

Subprocess Environment Action
=============================

This set of attributes specifies an action to alter the subprocess execution
environment. All explicit attributes shall be specified. The explicit
attributes for this type are:

action
    The attribute value shall be a string. It shall be the subprocess execution
    environment modification action.

name
    The attribute value shall be an optional string. If the value is present,
    then it shall be the environment variable name.

value
    The attribute value shall be an optional string. If the value is present,
    then it shall be the environment variable value.

This type is used by the following types:

- :ref:`SpecTypeSubprocessAction`

.. _SpecTypeUID:

UID
===

The value shall be a string. It shall be a valid absolute or relative item UID.

This type is used by the following types:

- :ref:`SpecTypeLink`
