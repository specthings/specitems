# SPDX-License-Identifier: BSD-2-Clause
"""Provides a function to verify the format of specification items.

This module provides the function :py:func:`verify_specification_format` to
verify that a set of specification items is in line with a specification item
format specification.  The format specification is defined by specification
items.  Logging is used for informational messages and for reporting errors
found during verification.  The result of the format verification is
represented by a :py:class:`VerifyStatus` object.
"""

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

from contextlib import contextmanager
import logging
import re
from typing import Any, Iterator, NamedTuple

from .items import Item, ItemCache

_VerifierMap = dict[str, "_Verifier"]


class VerifyStatus(NamedTuple):
    """Counts of log messages produced by a verification run.

    Attributes:
        critical: Number of CRITICAL messages.
        error: Number of ERROR messages.
        warning: Number of WARNING messages.
        info: Number of INFO messages.
        debug: Number of DEBUG messages.
    """
    critical: int
    error: int
    warning: int
    info: int
    debug: int


class _Filter(logging.Filter):

    def __init__(self) -> None:
        super().__init__()
        self._counts: dict[int, int] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Count the given logging record and allow propagation.

        Args:
            record: The logging record to count.

        Returns:
            True so the log record is processed by the logging system.
        """
        count = self._counts.get(record.levelno, 0)
        self._counts[record.levelno] = count + 1
        return True

    def get_verify_info(self) -> VerifyStatus:
        """Return a VerifyStatus summarizing collected log counts.

        Returns:
            Aggregated counts for each standard logging level.
        """
        return VerifyStatus(self._counts.get(logging.CRITICAL, 0),
                            self._counts.get(logging.ERROR, 0),
                            self._counts.get(logging.WARNING, 0),
                            self._counts.get(logging.INFO, 0),
                            self._counts.get(logging.DEBUG, 0))


def _type_name(value: Any):
    type_name = type(value).__name__
    if type_name == "NoneType":
        return "none"
    return type_name


class _Path(NamedTuple):
    item: Item
    path: str


class _AssertContext(NamedTuple):
    path: _Path
    value: Any
    type_info: dict[str, Any]
    ops: dict[str, Any]


def _assert_op_and(ctx: _AssertContext, assert_info: Any) -> bool:
    for element in assert_info:
        if not _assert(ctx, element):
            return False
    return True


def _assert_op_not(ctx: _AssertContext, assert_info: Any) -> bool:
    return not _assert(ctx, assert_info)


def _assert_op_or(ctx: _AssertContext, assert_info: Any) -> bool:
    for element in assert_info:
        if _assert(ctx, element):
            return True
    return False


def _assert_op_eq(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value == assert_info


def _assert_op_ne(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value != assert_info


def _assert_op_le(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value <= assert_info


def _assert_op_lt(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value < assert_info


def _assert_op_ge(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value >= assert_info


def _assert_op_gt(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value > assert_info


def _assert_op_uid(ctx: _AssertContext, _assert_info: Any) -> bool:
    try:
        ctx.path.item.map(ctx.value)
    except KeyError:
        logging.warning("%s cannot resolve UID: %s", _prefix(ctx.path),
                        ctx.value)
        return False
    return True


def _assert_op_re(ctx: _AssertContext, assert_info: Any) -> bool:
    return re.search(assert_info, ctx.value) is not None


def _assert_op_in(ctx: _AssertContext, assert_info: Any) -> bool:
    return ctx.value in assert_info


_WORD_SEPARATOR = re.compile(r"[ \t\n\r\f\v-]+")


def _assert_op_contains(ctx: _AssertContext, assert_info: Any) -> bool:
    value = " " + " ".join(_WORD_SEPARATOR.split(ctx.value.lower())) + " "
    return any(f" {substring} " in value for substring in assert_info)


def _assert(ctx: _AssertContext, assert_info: Any) -> bool:
    if isinstance(assert_info, list):
        return _assert_op_or(ctx, assert_info)
    key = next(iter(assert_info))
    return ctx.ops[key](ctx, assert_info[key])


def _maybe_assert(path: _Path, value: Any, type_info: Any,
                  ops: dict[str, Any]) -> bool:
    if "assert" in type_info:
        return _assert(_AssertContext(path, value, type_info, ops),
                       type_info["assert"])
    return True


_ASSERT_OPS_INT_OR_FLOAT = {
    "and": _assert_op_and,
    "not": _assert_op_not,
    "or": _assert_op_or,
    "eq": _assert_op_eq,
    "ne": _assert_op_ne,
    "le": _assert_op_le,
    "lt": _assert_op_lt,
    "ge": _assert_op_ge,
    "gt": _assert_op_gt,
}


def _assert_int_or_float(path: _Path, value: Any, type_info: Any) -> bool:
    return _maybe_assert(path, value, type_info, _ASSERT_OPS_INT_OR_FLOAT)


_ASSERT_OPS_STR = {
    "and": _assert_op_and,
    "not": _assert_op_not,
    "or": _assert_op_or,
    "eq": _assert_op_eq,
    "ne": _assert_op_ne,
    "le": _assert_op_le,
    "lt": _assert_op_lt,
    "ge": _assert_op_ge,
    "gt": _assert_op_gt,
    "uid": _assert_op_uid,
    "re": _assert_op_re,
    "in": _assert_op_in,
    "contains": _assert_op_contains,
}


def _assert_str(path: _Path, value: Any, type_info: Any) -> bool:
    return _maybe_assert(path, value, type_info, _ASSERT_OPS_STR)


def _assert_type(path: _Path, value: Any, type_expected: str) -> bool:
    type_actual = _type_name(value)
    if type_actual == type_expected:
        return True
    logging.error("%s expected type '%s', actual type '%s'", _prefix(path),
                  type_expected, type_actual)
    return False


NAME = re.compile(r"^([a-z][a-z0-9-]*|SPDX-License-Identifier)$")


def _prefix(prefix: _Path) -> str:
    if prefix.path.endswith(":"):
        return prefix.path
    return prefix.path + ":"


class _Verifier:

    def __init__(self, name: str, verifier_map: _VerifierMap):
        self._name = name
        self._verifier_map = verifier_map
        self.is_subtype = False
        verifier_map[name] = self

    def verify_info(self, path: _Path) -> None:
        """Log that verification is being performed for the given path.

        Args:
            path: Path context describing the location being verified.
        """
        logging.info("%s verify using type '%s'", _prefix(path), self._name)

    def verify(self, path: _Path, value: Any) -> set[str]:
        """Verify the value at the path.

        Check that the value matches the properties of the verifier.  Produce
        log messages with verification information and status.

        Args:
            path: Path context for logging and UID resolution.
            value: The value to verify.

        Returns:
            A set of keys that were verified.
        """
        self.verify_info(path)
        _assert_type(path, value, self._name)
        return set()

    def resolve_type_refinements(self) -> None:
        """Resolve type refinments.

        This hook may be used by composite verifiers to resolve type
        refinements.
        """


class _AnyVerifier(_Verifier):

    def verify(self, path: _Path, _value: Any) -> set[str]:
        """Accept any value without performing checks.

        Args:
            path: Path context (used only for logging).
            _value: Value to accept.

        Returns:
            Empty set.
        """
        self.verify_info(path)
        return set()


class _NameVerifier(_Verifier):

    def verify(self, path: _Path, value: Any) -> set[str]:
        """Verify that the value is a valid name string.

        Args:
            path: Path context.
            value: The value expected to be a string conforming to NAME.

        Returns:
            Empty set. Logs an error if the value is not a valid name.
        """
        self.verify_info(path)
        if _assert_type(path, value, "str") and NAME.search(value) is None:
            logging.error("%s invalid name: %s", _prefix(path), value)
        return set()


class _UIDVerifier(_Verifier):

    def verify(self, path: _Path, value: Any) -> set[str]:
        """Verify that the UID string can be resolved in the item's mapping
           context.

        Args:
            path: Path context whose item will be used to resolve the UID.
            value: The UID string to resolve.

        Returns:
            Empty set. Logs an error if the UID cannot be resolved.
        """
        self.verify_info(path)
        if _assert_type(path, value, "str"):
            try:
                path.item.map(value)
            except KeyError:
                logging.error("%s cannot resolve UID: %s", _prefix(path),
                              value)
        return set()


class _ItemVerifier(_Verifier):
    """Verifier for specification types that are described by a specification
       item.

    This class implements verification for structured types (dict/list/str/...)
    according to the specified type format.
    """

    def __init__(self, name: str, verifier_map: _VerifierMap,
                 info_map: dict[str, Any], item: Item):
        super().__init__(name, verifier_map)
        self._info_map = info_map
        self._item = item
        self._subtype_key = ""
        self._subtype_verifiers: _VerifierMap = {}

    def verify_bool(self, path: _Path, value: Any, type_info: Any) -> set[str]:
        """Verify a boolean value according to an optional assertion.

        Args:
            path: Path context.
            value: Boolean value to verify.
            type_info: Type info that may include an 'assert' field.

        Returns:
            Empty set. Logs an error if the assertion fails.
        """
        if type_info and "assert" in type_info:
            expected = type_info["assert"]
            if expected != value:
                logging.error("%s expected %r, actual %r", _prefix(path),
                              expected, value)
        return set()

    def _verify_key(self, path: _Path, value: Any, type_name: str,
                    key: str) -> None:
        if type_name in self._verifier_map:
            self._verifier_map[type_name].verify(
                _Path(path.item, path.path + f"/{key}"), value[key])
        else:
            logging.error("%s unknown specification type: %s", _prefix(path),
                          type_name)

    def assert_keys_no_constraints(self, _path: _Path,
                                   _specified_keys: set[str],
                                   _keys: list[str]) -> None:
        """No-op key assertion.

        Args:
            _path: Path context (unused).
            _specified_keys: Set of keys that would be checked (unused).
            _keys: Keys present in the instance being validated (unused).
        """

    def assert_keys_at_least_one(self, path: _Path, specified_keys: set[str],
                                 keys: list[str]) -> None:
        """Assert that at least one of specified_keys is present.

        Args:
            path: Path context.
            specified_keys: Set of keys where at least one must be present.
            keys: Keys actually present.

        Logs an error if none of specified_keys are present.
        """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) == 0:
            logging.error(
                "%s not at least one key out of %s is present for type '%s'",
                _prefix(path), sorted(specified_keys), self._name)

    def assert_keys_at_most_one(self, path: _Path, specified_keys: set[str],
                                keys: list[str]) -> None:
        """Assert that at most one of specified_keys is present.

        Args:
            path: Path context.
            specified_keys: Set of keys where at most one may be present.
            keys: Keys actually present.

        Logs an error if more than one of specified_keys are present.
        """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) > 1:
            logging.error(
                "%s not at most one key out of %s "
                "is present for type '%s': %s", _prefix(path),
                sorted(specified_keys), self._name, sorted(present_keys))

    def assert_keys_exactly_one(self, path: _Path, specified_keys: set[str],
                                keys: list[str]) -> None:
        """Assert that exactly one of specified_keys is present.

        Args:
            path: Path context.
            specified_keys: Set of keys where exactly one must be present.
            keys: Keys actually present.

        Logs an error if not exactly one of specified_keys is present.
        """
        present_keys = specified_keys.intersection(keys)
        if len(present_keys) != 1:
            logging.error(
                "%s not exactly one key out of %s "
                "is present for type '%s': %s", _prefix(path),
                sorted(specified_keys), self._name, sorted(present_keys))

    def assert_keys_subset(self, path: _Path, specified_keys: set[str],
                           keys: list[str]) -> None:
        """Assert that specified_keys is a subset of keys.

        Args:
            path: Path context.
            specified_keys: Required keys.
            keys: Keys actually present.

        Logs an error if any required keys are missing.
        """
        if not specified_keys.issubset(keys):
            missing_keys = specified_keys.difference(
                specified_keys.intersection(keys))
            logging.error("%s missing mandatory keys for type '%s': %s",
                          _prefix(path), self._name, sorted(missing_keys))

    def _assert_mandatory_keys(self, path: _Path, type_info: Any,
                               attr_info: Any, keys: list[str]) -> None:
        mandatory_attr_info = type_info["mandatory-attributes"]
        if isinstance(mandatory_attr_info, str):
            _ASSERT_KEYS[mandatory_attr_info](self, path, set(attr_info), keys)
        else:
            assert isinstance(mandatory_attr_info, list)
            self.assert_keys_subset(path, set(mandatory_attr_info), keys)

    def verify_dict(self, path: _Path, value: Any, type_info: Any) -> set[str]:
        """Verify a dictionary-typed value against type_info.

        The method:
        - ensures mandatory attributes are present,
        - delegates verification of known attributes to their spec-type
          verifiers,
        - handles generic-attributes if present (validates key and value
          types),
        - handles subtype dispatching if refinements were declared, and
        - reports unverified keys when appropriate.

        Args:
            path: Path context for the dict value.
            value: The dict to verify.
            type_info: The 'dict' variant type_info for this spec-type.

        Returns:
            A set of keys that were verified by this call (useful when
            a parent verifier aggregates verified keys).
        """
        keys = sorted(value.keys())
        attr_info = type_info["attributes"]
        self._assert_mandatory_keys(path, type_info, attr_info, keys)
        verified_keys: set[str] = set()
        for key in keys:
            if key in attr_info:
                self._verify_key(path, value, attr_info[key]["spec-type"], key)
                verified_keys.add(key)
            elif "generic-attributes" in type_info:
                key_as_value = {key: key}
                self._verify_key(
                    path, key_as_value,
                    type_info["generic-attributes"]["key-spec-type"], key)
                self._verify_key(
                    path, value,
                    type_info["generic-attributes"]["value-spec-type"], key)
                verified_keys.add(key)
        if self._subtype_key:
            if self._subtype_key in keys:
                subtype_value = value[self._subtype_key]
                if subtype_value in self._subtype_verifiers:
                    verified_keys.update(
                        self._subtype_verifiers[subtype_value].verify(
                            path, value))
                else:
                    logging.error(
                        "%s unknown subtype for key '%s' for type '%s': %s",
                        _prefix(path), self._subtype_key, self._name,
                        subtype_value)
            else:
                logging.error("%s subtype key '%s' not present for type '%s'",
                              _prefix(path), self._subtype_key, self._name)
        if not self.is_subtype:
            unverified_keys = set(keys).difference(verified_keys)
            if unverified_keys:
                logging.error(
                    "%s has unverfied keys for type '%s' and its subtypes: %s",
                    _prefix(path), self._name, sorted(unverified_keys))
        return verified_keys

    def verify_int_or_float(self, path: _Path, value: Any,
                            type_info: Any) -> set[str]:
        """Verify an integer or float value according to the numeric
           assertions.

        Args:
            path: Path context.
            value: The numeric value to verify.
            type_info: Type info containing numeric 'assert' conditions.

        Returns:
            Empty set. Logs an error if assertions fail.
        """
        if not _assert_int_or_float(path, value, type_info):
            logging.error("%s invalid value: %s", _prefix(path), value)
        return set()

    def verify_list(self, path: _Path, value: Any, type_info: Any) -> set[str]:
        """Verify a list by delegating verification to an element verifier.

        Args:
            path: Path context for the list.
            value: List of elements to verify.
            type_info: Type info containing 'spec-type' naming the element
                type.

        Returns:
            Empty set. Element verification is delegated to another verifier.
        """
        verifier = self._verifier_map[type_info["spec-type"]]
        for index, element in enumerate(value):
            verifier.verify(_Path(path.item, path.path + f"[{index}]"),
                            element)
        return set()

    def verify_none(self, _path: _Path, _value: Any,
                    _type_info: Any) -> set[str]:
        """Verify a None (null) value.

        Args:
            _path: Path context (unused).
            _value: Value expected to be None.
            _type_info: Type info for the 'none' variant (unused).

        Returns:
            Empty set.
        """
        return set()

    def verify_str(self, path: _Path, value: Any, type_info: Any) -> set[str]:
        """Verify a string value using string-specific assertions.

        Args:
            path: Path context.
            value: The string to verify.
            type_info: Type info that may contain string 'assert' expressions.

        Returns:
            Empty set. Logs an error if assertions fail.
        """
        if not _assert_str(path, value, type_info):
            logging.error("%s invalid value: %s", _prefix(path), value)
        return set()

    def verify(self, path: _Path, value: Any) -> set[str]:
        """Top-level dispatch to the appropriate primitive verifier.

        Args:
            path: Path context for the value.
            value: Python value to verify.

        Returns:
            A set of keys verified by the invoked verifier (may be empty).
        """
        self.verify_info(path)
        type_name = _type_name(value)
        if type_name in self._info_map:
            return _VERIFY[type_name](self, path, value,
                                      self._info_map[type_name])
        logging.error(
            "%s expected value of types %s for type '%s', "
            "actual type '%s'", _prefix(path), sorted(self._info_map),
            self._name, type_name)
        return set()

    def _add_subtype_verifier(self, subtype_key: str, subtype_value: str,
                              subtype_name: str) -> None:
        logging.info("add subtype '%s' to '%s'", subtype_name, self._name)
        assert not self._subtype_key or self._subtype_key == subtype_key
        assert subtype_value not in self._subtype_verifiers
        subtype_verifier = self._verifier_map[subtype_name]
        subtype_verifier.is_subtype = True
        self._subtype_key = subtype_key
        self._subtype_verifiers[subtype_value] = subtype_verifier

    def resolve_type_refinements(self) -> None:
        for link in self._item.links_to_children():
            if link.role == "spec-refinement":
                self._add_subtype_verifier(link["spec-key"],
                                           link["spec-value"],
                                           link.item["spec-type"])


_VERIFY = {
    "bool": _ItemVerifier.verify_bool,
    "dict": _ItemVerifier.verify_dict,
    "float": _ItemVerifier.verify_int_or_float,
    "int": _ItemVerifier.verify_int_or_float,
    "list": _ItemVerifier.verify_list,
    "none": _ItemVerifier.verify_none,
    "str": _ItemVerifier.verify_str,
}

_ASSERT_KEYS = {
    "all": _ItemVerifier.assert_keys_subset,
    "at-least-one": _ItemVerifier.assert_keys_at_least_one,
    "at-most-one": _ItemVerifier.assert_keys_at_most_one,
    "exactly-one": _ItemVerifier.assert_keys_exactly_one,
    "none": _ItemVerifier.assert_keys_no_constraints,
}


def _create_verifier(item: Item, verifier_map: _VerifierMap) -> _Verifier:
    spec_type = item["spec-type"]
    if spec_type in verifier_map:
        verifier = verifier_map[spec_type]
        assert isinstance(verifier, (_NameVerifier, _UIDVerifier))
        return verifier
    spec_info = item["spec-info"]
    assert isinstance(spec_info, dict)
    return _ItemVerifier(spec_type, verifier_map, spec_info, item)


def _gather_item_verifiers(item: Item, verifier_map: _VerifierMap) -> None:
    for link in item.links_to_children():
        if link.role == "spec-member":
            _create_verifier(link.item, verifier_map)


@contextmanager
def _add_filter() -> Iterator[_Filter]:
    logger = logging.getLogger()
    log_filter = _Filter()
    logger.addFilter(log_filter)
    yield log_filter
    logger.removeFilter(log_filter)


class SpecVerifier:
    """Orchestrates construction of verifiers from spec items and running
    verification.

    The SpecVerifier builds a map of verifiers by walking specification type
    definitions starting from the root type.  It registers primitive verifiers
    (any, name, uid, str/int/float/bool/none) and then creates _ItemVerifier
    instances for each specification type referenced by the root type.  After
    creation, it resolves subtype refinements and is ready to verify items.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, item_cache: ItemCache, root_uid: str):
        """Initialize and build verifier map.

        Args:
            item_cache: ItemCache providing access to specification type items
                and to instances that need verification.
            root_uid: UID of the root specification type item (entry point for
                the specification type tree). If the root UID is missing the
                verifier will be left uninitialized and verification methods
                will report an error.
        """
        verifier_map: _VerifierMap = {}
        _AnyVerifier("any", verifier_map)
        _NameVerifier("name", verifier_map)
        _UIDVerifier("uid", verifier_map)
        _Verifier("bool", verifier_map)
        _Verifier("float", verifier_map)
        _Verifier("int", verifier_map)
        _Verifier("none", verifier_map)
        _Verifier("str", verifier_map)
        try:
            root_item = item_cache[root_uid]
        except KeyError:
            self._root_verifier = None
        else:
            self._root_verifier = _create_verifier(root_item, verifier_map)
            _gather_item_verifiers(root_item, verifier_map)
            for name in sorted(verifier_map):
                logging.info("type: %s", name)
                verifier_map[name].resolve_type_refinements()

    def verify_all(self, item_cache: ItemCache) -> VerifyStatus:
        """Verify all items in the provided item cache.

        The method installs a logging filter to collect counts, iterates all
        items in the cache and invokes the root verifier on each item's data.

        Args:
            item_cache: The cache containing items to verify.

        Returns:
            Status with counts of messages emitted during verification.
        """
        with _add_filter() as log_filter:
            if self._root_verifier is None:
                logging.error("root type item does not exist in item cache")
            else:
                logging.info("start specification item verification")
                for key in sorted(item_cache):
                    item = item_cache[key]
                    self._root_verifier.verify(_Path(item, f"{item.uid}:"),
                                               item.data)
                logging.info("finished specification item verification")
        return log_filter.get_verify_info()

    def verify(self, item: Item) -> VerifyStatus:
        """Verify the item format.

        Args:
            item: Item instance to verify.

        Returns:
            Status with counts of messages emitted during verification.
        """
        with _add_filter() as log_filter:
            if self._root_verifier is None:
                logging.error("root type item does not exist in item cache")
            else:
                self._root_verifier.verify(_Path(item, f"{item.uid}:"),
                                           item.data)
        return log_filter.get_verify_info()


def verify_specification_format(item_cache: ItemCache) -> VerifyStatus:
    """Verify all items using the specification root type from the item cache.

    Emits an error if the item cache has no specification root type.

    Args:
        item_cache: The item cache containing the items to verify.

    Returns:
        The status summarizing the verification run.
    """
    root_type_uid = item_cache.type_provider.root_type_uid
    if root_type_uid is None:
        logging.error("item cache has no root type")
        return VerifyStatus(0, 1, 0, 0, 0)
    verifier = SpecVerifier(item_cache, root_type_uid)
    return verifier.verify_all(item_cache)
