# SPDX-License-Identifier: BSD-2-Clause
""" Provides support for SPDX license expressions. """

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

import functools
import importlib.metadata
import re
from typing import Any

import license_expression

#: Matches a license reference of SPDX 2.3, Annex D.
LICENSE_REF = re.compile(r"^(DocumentRef-[A-Za-z0-9.\-]+:)?"
                         r"LicenseRef-[A-Za-z0-9.\-]+$")


@functools.lru_cache(maxsize=1)
def get_licensing() -> license_expression.Licensing:
    """ Get the SPDX licensing which holds the SPDX License List. """
    return license_expression.get_spdx_licensing()


def get_license_list_version() -> str:
    """
    Get the version of the package which provides the SPDX License List.

    The package exposes no version of the list itself, so the version of the
    package identifies the accepted vocabulary.
    """
    return importlib.metadata.version("license-expression")


def _check_vocabulary(text: str, expression: Any) -> None:
    unknown = sorted(
        symbol.key
        for symbol in get_licensing().unknown_license_symbols(expression)
        if LICENSE_REF.match(symbol.key) is None)
    if unknown:
        raise ValueError(f"SPDX license expression '{text}' uses unknown "
                         f"identifiers: {', '.join(unknown)}")


def parse_license_expression(text: str) -> Any:
    """
    Parse the SPDX license expression.

    Accept an identifier of the SPDX License List and a license reference such
    as ``LicenseRef-ECSS``.  Demand the canonical form of every identifier, so
    a deprecated form such as ``GPL-2.0+`` is an error.

    Args:
        text: The SPDX license expression.

    Returns:
        The parsed expression.

    Raises:
        ValueError: The expression is malformed, it uses an unknown
            identifier, or it is not in canonical form.
    """
    try:
        expression = get_licensing().parse(text, validate=False, strict=True)
    except license_expression.ExpressionError as err:
        raise ValueError(
            f"invalid SPDX license expression '{text}': {err}") from err
    if expression is None:
        raise ValueError("empty SPDX license expression")
    _check_vocabulary(text, expression)
    canonical = str(expression)
    if canonical != text:
        raise ValueError(f"SPDX license expression '{text}' is not "
                         f"canonical, use '{canonical}'")
    return expression


def parse_license_identifier(text: str) -> str:
    """
    Parse a single SPDX license identifier.

    Args:
        text: The SPDX license identifier.

    Returns:
        The identifier.

    Raises:
        ValueError: The value is no single identifier of the SPDX License
            List and no license reference.
    """
    expression = parse_license_expression(text)
    if not isinstance(expression, license_expression.LicenseSymbol):
        raise ValueError(f"'{text}' is no single SPDX license identifier")
    return text


def _is_satisfied(expression: Any, the_license: str) -> bool:
    licensing = get_licensing()
    if isinstance(expression, licensing.AND):
        return all(
            _is_satisfied(argument, the_license)
            for argument in expression.args)
    if isinstance(expression, licensing.OR):
        return any(
            _is_satisfied(argument, the_license)
            for argument in expression.args)
    return str(expression) == the_license


def permits(text: str, the_license: str) -> bool:
    """
    Tell whether the SPDX license expression permits the license.

    The expression permits the license if it evaluates to true where this
    license is true and every other license is false.  An expression of
    ``A AND B`` permits no single license.

    Args:
        text: The SPDX license expression.
        the_license: The SPDX license identifier.

    Returns:
        True if the expression permits the license, otherwise false.

    Raises:
        ValueError: The expression is invalid.
    """
    return _is_satisfied(parse_license_expression(text), the_license)
