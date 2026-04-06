# SPDX-License-Identifier: BSD-2-Clause
""" Provides a function to document specification items. """

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

import dataclasses
import re
from typing import Any, Callable, Iterator, Optional, Pattern

from .contenttext import make_label, TextContent
from .items import Item, ItemCache
from .itemmapper import ItemGetValueContext, ItemMapper


@dataclasses.dataclass
class SpecDocumentConfig:
    """ Represents a specification item type document configuration. """
    # pylint: disable=too-many-instance-attributes
    target: str = "items.md"
    root_type_uid: str = "/spec/root"
    ignore: str = "^$"
    label_prefix: str = "SpecType"
    section_label_prefix: str = ""
    hierarchy_text: str = ("The specification item types "
                           "have the following hierarchy:")
    section_name: str = "Specification items"
    hierarchy_subsection_name: str = "Specification item hierarchy"
    item_types_subsection_name: str = "Specification item types"
    value_types_subsection_name: str = ("Specification attribute "
                                        "sets and value types")


_DocumenterMap = dict[str, "_Documenter"]

_PRIMITIVE_TYPES = {
    "any": "The attribute value may have any type.",
    "bool": "{} {} be a boolean.",
    "float": "{} {} be a floating-point number.",
    "int": "{} {} be an integer number.",
    "list-str": "{} {} be a list of strings.",
    "none": "The attribute shall have no value.",
    "optional-str": "{} {} be an optional string.",
    "str": "{} {} be a string.",
}

_MANDATORY_ATTRIBUTES = {
    "all":
    "All explicit attributes shall be specified.",
    "at-least-one":
    "At least one of the explicit attributes shall be specified.",
    "at-most-one":
    "At most one of the explicit attributes shall be specified.",
    "exactly-one":
    "Exactly one of the explicit attributes shall be specified.",
    "none":
    "None of the explicit attributes is mandatory, "
    "they are all optional.",
}


def _a_or_an(value: str) -> str:
    if value[0].lower() in ["a", "e", "i", "o", "u"]:
        return "an"
    return "a"


class _AssertContext:
    """ Provides a context to document assert expressions. """

    def __init__(self, content: TextContent, ops: dict[str, Any]):
        self.content = content
        self.ops = ops
        self._comma = ""

    def comma(self):
        """ Add a comma to the content if necessary. """
        if not self.content.last.endswith(","):
            self.content.last += self._comma
            self._comma = ","

    def paste(self, text: str):
        """ Paste a text to the content. """
        self.content.paste(text)

    def value(self, value: Any) -> str:
        """ Return the value as text. """
        if isinstance(value, str):
            return f"\"{self.content.code(value)}\""
        if isinstance(value, bool):
            if value:
                value = "true"
            else:
                value = "false"
        else:
            value = str(value)
        return self.content.code(value)


def _negate(negate: bool) -> str:
    if negate:
        return "not "
    return ""


def _list(ctx: _AssertContext, assert_info: list[str]) -> None:
    ctx.content.add_list(
        [f"{ctx.value(value)}," for value in assert_info[:-2]])
    try:
        ctx.content.add_list_item(f"{ctx.value(assert_info[-2])}, and")
    except IndexError:
        pass
    try:
        ctx.content.add_list_item(f"{ctx.value(assert_info[-1])}")
    except IndexError:
        pass


def _document_op_and_or(ctx: _AssertContext, negate: bool, assert_info: Any,
                        and_or: str) -> None:
    if len(assert_info) == 1:
        _document_assert(ctx, negate, assert_info[0])
    else:
        if negate or ctx.content.is_at_empty_list_item():
            ctx.paste(f"shall {_negate(negate)}meet")
        intro = ""
        for element in assert_info:
            ctx.comma()
            with ctx.content.list_item(intro):
                _document_assert(ctx, False, element)
            intro = and_or


def _document_op_and(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    _document_op_and_or(ctx, negate, assert_info, "and, ")


def _document_op_not(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    _document_assert(ctx, not negate, assert_info)


def _document_op_or(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    _document_op_and_or(ctx, negate, assert_info, "or, ")


def _document_op_eq(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_ne(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be equal to {ctx.value(assert_info)}")


def _document_op_ne(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_eq(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be not equal to {ctx.value(assert_info)}")


def _document_op_le(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_gt(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be less than or equal to {ctx.value(assert_info)}")


def _document_op_lt(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_ge(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be less than {ctx.value(assert_info)}")


def _document_op_ge(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_lt(ctx, False, assert_info)
    else:
        ctx.paste(
            f"shall be greater than or equal to {ctx.value(assert_info)}")


def _document_op_gt(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    if negate:
        _document_op_le(ctx, False, assert_info)
    else:
        ctx.paste(f"shall be greater than {ctx.value(assert_info)}")


def _document_op_uid(ctx: _AssertContext, negate: bool,
                     _assert_info: Any) -> None:
    if negate:
        ctx.paste("shall be an invalid item UID")
    else:
        ctx.paste("shall be a valid item UID")


def _document_op_re(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}match with "
              f"the regular expression {ctx.value(assert_info)}")


def _document_op_in(ctx: _AssertContext, negate: bool,
                    assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}be an element of")
    _list(ctx, assert_info)


def _document_op_contains(ctx: _AssertContext, negate: bool,
                          assert_info: Any) -> None:
    ctx.paste(f"shall {_negate(negate)}contain an element of")
    _list(ctx, assert_info)


def _document_assert(ctx: _AssertContext, negate: bool,
                     assert_info: Any) -> None:
    if isinstance(assert_info, bool):
        if negate:
            assert_info = not assert_info
        ctx.paste(f"shall be {ctx.value(assert_info)}")
    elif isinstance(assert_info, list):
        _document_op_or(ctx, negate, assert_info)
    else:
        key = next(iter(assert_info))
        ctx.ops[key](ctx, negate, assert_info[key])


_DOCUMENT_OPS = {
    "and": _document_op_and,
    "contains": _document_op_contains,
    "eq": _document_op_eq,
    "ge": _document_op_ge,
    "gt": _document_op_gt,
    "in": _document_op_in,
    "le": _document_op_le,
    "lt": _document_op_lt,
    "ne": _document_op_ne,
    "not": _document_op_not,
    "or": _document_op_or,
    "re": _document_op_re,
    "uid": _document_op_uid,
}


def _maybe_document_assert(content: TextContent, type_info: Any) -> None:
    assert_info = type_info.get("assert", None)
    if assert_info:
        content.paste("The value ")
        _document_assert(_AssertContext(content, _DOCUMENT_OPS), False,
                         assert_info)
        content.last += "."


class _Documenter:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, mapper: ItemMapper, item: Item,
                 documenter_map: _DocumenterMap, label_prefix: str,
                 content: TextContent):
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-positional-arguments
        self._present = False
        self._mapper = mapper
        self._name = item["spec-type"]
        self.section = item["spec-name"]
        self._info_map = item["spec-info"]
        self._item = item
        self._documenter_map = documenter_map
        self.used_by: set[str] = set()
        self._label_prefix = label_prefix
        self._content = content
        self._description = self._substitute(item["spec-description"])
        assert self._name not in documenter_map
        documenter_map[self._name] = self

    def _substitute(self, text: Optional[str]) -> str:
        return self._mapper.substitute(text, self._item)

    def get_section_reference(self) -> str:
        """ Return the section reference. """
        return self._content.get_reference(self._label_prefix +
                                           make_label(self.section))

    def get_a_section_reference(self) -> str:
        """ Return a section reference. """
        return f"{_a_or_an(self.section)} {self.get_section_reference()}"

    def get_list_element_type(self) -> str:
        """ Return the list element type if this is a list only type. """
        if len(self._info_map) == 1 and "list" in self._info_map:
            return self._info_map["list"]["spec-type"]
        return ""

    def get_list_phrase(self, value: str, shall: str, type_name: str) -> str:
        """ Return a list phrase. """
        if type_name in _PRIMITIVE_TYPES:
            type_phrase = _PRIMITIVE_TYPES[type_name].format(
                "Each list element", "shall")
        else:
            documenter = self._documenter_map[type_name]
            ref = documenter.get_a_section_reference()
            type_phrase = f"Each list element shall be {ref}."
        return f"{value} {shall} be a list. {type_phrase}"

    def get_value_type_phrase(self, value: str, shall: str,
                              type_name: str) -> str:
        """ Return a value type phrase. """
        if type_name in _PRIMITIVE_TYPES:
            return _PRIMITIVE_TYPES[type_name].format(value, shall)
        documenter = self._documenter_map[type_name]
        element_type_name = documenter.get_list_element_type()
        if element_type_name:
            return self.get_list_phrase(value, shall, element_type_name)
        return (f"{value} {shall} be "
                f"{documenter.get_a_section_reference()}.")

    def refinements(self, ignore: Pattern[Any]) -> Iterator["_Documenter"]:
        """ Yield the refinements of this type. """
        refinement_set = set(
            self._documenter_map[child["spec-type"]]
            for child in self._item.children("spec-refinement")
            if ignore.search(child["spec-type"]) is None)
        yield from sorted(refinement_set, key=lambda x: x.section)

    def refines(self) -> Iterator[tuple["_Documenter", str, str]]:
        """ Yield the types refined by type. """
        refines = [(self._documenter_map[link.item["spec-type"]],
                    link["spec-key"], link["spec-value"])
                   for link in self._item.links_to_parents()
                   if link.role == "spec-refinement"]
        yield from sorted(refines, key=lambda x: x[0].section)

    def hierarchy(self, ignore) -> None:
        """ Document the item type hierarchy. """
        with self._content.list_item(self.get_section_reference()):
            for refinement in self.refinements(ignore):
                refinement.hierarchy(ignore)

    def _document_attributes(self, attributes: Any) -> None:
        for key in sorted(attributes):
            info = attributes[key]
            definition = self.get_value_type_phrase("The attribute value",
                                                    "shall", info["spec-type"])
            description = info["description"]
            definition = f"{definition}\n{self._substitute(description)}"
            self._content.add_definition_item(key, definition)

    def document_dict(self, _variant: str, shall: str, info: Any) -> None:
        """ Document an attribute set. """
        if shall == "may":
            self._content.paste("The value may be a set of attributes.")
        self._content.paste(self._substitute(info["description"]))
        has_explicit_attributes = len(info["attributes"]) > 0
        if has_explicit_attributes:
            mandatory_attributes = info["mandatory-attributes"]
            if isinstance(mandatory_attributes, str):
                self._content.paste(
                    _MANDATORY_ATTRIBUTES[mandatory_attributes])
            else:
                assert isinstance(mandatory_attributes, list)
                mandatory_attribute_count = len(mandatory_attributes)
                if mandatory_attribute_count == 1:
                    self._content.paste(
                        "Only the "
                        f"{self._content.code(mandatory_attributes[0])} "
                        "attribute is mandatory.")
                elif mandatory_attribute_count > 1:
                    self._content.paste("The following explicit "
                                        "attributes are mandatory:")
                    for attribute in sorted(mandatory_attributes):
                        self._content.add_list_item(
                            self._content.code(attribute))
                    self._content.ensure_blank_line()
                else:
                    self._content.ensure_blank_line()
            self._content.paste("The explicit attributes for this type are:")
            self._document_attributes(info["attributes"])
        if "generic-attributes" in info:
            if has_explicit_attributes:
                self._content.wrap("In addition to the explicit attributes, "
                                   "generic attributes may be specified.")
            else:
                self._content.paste("Generic attributes may be specified.")
            self._content.paste(
                self.get_value_type_phrase(
                    "Each generic attribute key", "shall",
                    info["generic-attributes"]["key-spec-type"]))
            self._content.paste(
                self.get_value_type_phrase(
                    "Each generic attribute value", "shall",
                    info["generic-attributes"]["value-spec-type"]))
            self._content.paste(
                self._substitute(info["generic-attributes"]["description"]))

    def document_value(self, variant: str, shall: str, info: Any) -> None:
        """ Document a value. """
        self._content.paste(
            self.get_value_type_phrase("The value", shall, variant))
        self._content.paste(self._substitute(info["description"]))
        _maybe_document_assert(self._content, info)

    def document_list(self, _variant: str, shall: str, info: Any) -> None:
        """ Document a list value. """
        self._content.paste(
            self.get_list_phrase("The value", shall, info["spec-type"]))
        self._content.paste(self._substitute(info["description"]))

    def document_none(self, _variant: str, shall: str, _info: Any) -> None:
        """ Document a none value. """
        self._content.paste(f"There {shall} be no value (null).")

    def _add_description(self) -> None:
        refines = [
            f"{documenter.get_section_reference()} through the "
            f"{self._content.code(key)} attribute if the value is "
            f"{self._content.code(value)}"
            for documenter, key, value in self.refines()
        ]
        if len(refines) == 1:
            self._content.wrap(f"This type refines the {refines[0]}.")
            self._content.paste(self._description)
        else:
            self._content.add_list(refines,
                                   "This type refines the following types:")
            self._content.wrap(self._description)
        if self._description:
            self._content.add_blank_line()

    def document(self,
                 ignore: Pattern[Any],
                 names: Optional[set[str]] = None) -> None:
        """ Document this type. """
        if self.get_list_element_type():
            return
        if not self._present:
            return
        self._content.register_license_and_copyrights_of_item(self._item)
        with self._content.section(
                self.section,
                label=f"{self._label_prefix}{make_label(self.section)}"):
            self._add_description()
            if len(self._info_map) == 1:
                key, info = next(iter(self._info_map.items()))
                _DOCUMENT[key](self, key, "shall", info)
            else:
                self._content.add("A value of this type shall be of one of "
                                  "the following variants:")
                for key in sorted(self._info_map):
                    with self._content.list_item(""):
                        _DOCUMENT[key](self, key, "may", self._info_map[key])
            self._content.add_list([
                refinement.get_section_reference()
                for refinement in self.refinements(ignore)
            ], "This type is refined by the following types:")
            self._content.add_list(
                sorted(self.used_by),
                "This type is used by the following types:")
            example = self._item["spec-example"]
            if example:
                self._content.add(
                    "Please have a look at the following example:")
                with self._content.directive("code-block", "yaml"):
                    self._content.add(example)
        if names:
            names.remove(self._name)
            for refinement in self.refinements(ignore):
                refinement.document(ignore, names)

    def _add_used_by(self, type_name: str, ignore: Pattern[Any]) -> None:
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            element_type_name = documenter.get_list_element_type()
            if element_type_name:
                documenter.resolve_used_by(ignore)
                type_name = element_type_name
        if type_name not in _PRIMITIVE_TYPES:
            documenter = self._documenter_map[type_name]
            documenter.used_by.add(self.get_section_reference())
            documenter.resolve_used_by(ignore)

    def resolve_used_by(self, ignore: Pattern[Any]) -> None:
        """ Resolve type uses in attribute sets. """
        if self._present:
            return
        self._present = True
        info = self._info_map.get("dict", None)
        if info is not None:
            for attribute in info["attributes"].values():
                self._add_used_by(attribute["spec-type"], ignore)
            if "generic-attributes" in info:
                self._add_used_by(info["generic-attributes"]["key-spec-type"],
                                  ignore)
                self._add_used_by(
                    info["generic-attributes"]["value-spec-type"], ignore)
        for refinement in self.refinements(ignore):
            refinement.resolve_used_by(ignore)


_DOCUMENT = {
    "bool": _Documenter.document_value,
    "dict": _Documenter.document_dict,
    "float": _Documenter.document_value,
    "int": _Documenter.document_value,
    "list": _Documenter.document_list,
    "none": _Documenter.document_none,
    "str": _Documenter.document_value,
}


def add_specification_documentation(content: TextContent,
                                    config: SpecDocumentConfig,
                                    item_cache: ItemCache,
                                    mapper: ItemMapper) -> None:
    """
    Add the specification item types documentation according to the
    configuration to the content.

    Args:
        content: The target content.
        config: The specification item type document configuration.
        item_cache: The item cache containing the specification types.
        mapper: The item mapper used for content substitutions.
    """

    def _get_ref_specification_type(ctx: ItemGetValueContext) -> str:
        return content.get_reference(config.label_prefix +
                                     make_label(ctx.value[ctx.key]))

    mapper.add_get_value("spec:/spec-name", _get_ref_specification_type)
    documenter_map: _DocumenterMap = {}
    root_item = item_cache[config.root_type_uid]
    root_documenter = _Documenter(mapper, root_item, documenter_map,
                                  config.label_prefix, content)
    ignore = re.compile(config.ignore)
    for member in root_item.children("spec-member"):
        if ignore.search(member["spec-type"]) is None:
            _Documenter(mapper, member, documenter_map, config.label_prefix,
                        content)
    root_documenter.resolve_used_by(ignore)
    documenter_names = set(documenter_map)
    content.push_label(config.section_label_prefix)
    with content.section(config.section_name):
        content.push_label(config.section_label_prefix)
        with content.section(config.hierarchy_subsection_name):
            content.add(config.hierarchy_text)
            root_documenter.hierarchy(ignore)
        with content.section(config.item_types_subsection_name):
            root_documenter.document(ignore, documenter_names)
        with content.section(config.value_types_subsection_name):
            documenters = [documenter_map[name] for name in documenter_names]
            for documenter in sorted(documenters, key=lambda x: x.section):
                documenter.document(ignore)


def generate_specification_documentation(
        config: SpecDocumentConfig, item_cache: ItemCache, mapper: ItemMapper,
        create_content: Callable[[], TextContent]) -> None:
    """
    Document the specification item types according to the configuration.

    Args:
        config: The specification item type document configuration.
        item_cache: The item cache containing the specification types.
        mapper: The item mapper used for content substitutions.
        create_content: The content builder constructor.
    """
    content = create_content()
    content.add_automatically_generated_warning()
    add_specification_documentation(content, config, item_cache, mapper)
    content.add_licence_and_copyrights()
    content.write(config.target, beautify=True)
