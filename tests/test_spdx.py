# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the spdx module. """

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

import pytest

from specitems.spdx import (get_license_list_version, parse_license_expression,
                            parse_license_identifier, permits)

# Expression, license, permitted.
# Expression, license, permitted.
_PERMITS = [
    ("MIT", "MIT", True),
    ("MIT", "BSD-2-Clause", False),
    ("CC-BY-SA-4.0 OR BSD-2-Clause", "CC-BY-SA-4.0", True),
    ("CC-BY-SA-4.0 OR BSD-2-Clause", "BSD-2-Clause", True),
    ("CC-BY-SA-4.0 OR BSD-2-Clause", "MIT", False),
    ("(MIT AND BSD-2-Clause) OR Apache-2.0", "Apache-2.0", True),
    ("(MIT AND BSD-2-Clause) OR Apache-2.0", "MIT", False),
    ("(MIT OR BSD-2-Clause) AND MIT", "MIT", True),
    ("MIT AND BSD-2-Clause", "MIT", False),
    ("MIT WITH LLVM-exception", "MIT", False),
    ("LicenseRef-ECSS", "LicenseRef-ECSS", True),
    ("DocumentRef-x:LicenseRef-y", "DocumentRef-x:LicenseRef-y", True),
]

# Expression, error message.
_EXPRESSION_ERROR = [
    ("", "empty SPDX license expression"),
    ("MIT OR", "invalid SPDX license expression 'MIT OR': OR requires two or "
     "more licenses as in: MIT OR BSD"),
    ("ECSS", "SPDX license expression 'ECSS' uses unknown identifiers: ECSS"),
    ("MIT OR Foo-1.0 OR Bar-2.0",
     "SPDX license expression 'MIT OR Foo-1.0 OR Bar-2.0' uses unknown "
     "identifiers: Bar-2.0, Foo-1.0"),
    ("mit", "SPDX license expression 'mit' is not canonical, use 'MIT'"),
    ("GPL-2.0+", "SPDX license expression 'GPL-2.0+' is not canonical, use "
     "'GPL-2.0-or-later'"),
]


def test_get_license_list_version():
    assert get_license_list_version()


@pytest.mark.parametrize("text, the_license, expected", _PERMITS)
def test_permits(text, the_license, expected):
    assert permits(text, the_license) is expected


@pytest.mark.parametrize("text, message", _EXPRESSION_ERROR)
def test_parse_license_expression_error(text, message):
    with pytest.raises(ValueError) as err:
        parse_license_expression(text)
    assert str(err.value) == message


def test_parse_license_identifier():
    assert parse_license_identifier("MIT") == "MIT"
    assert parse_license_identifier("LicenseRef-ECSS") == "LicenseRef-ECSS"
    with pytest.raises(ValueError) as err:
        parse_license_identifier("MIT OR BSD-2-Clause")
    assert str(err.value) == ("'MIT OR BSD-2-Clause' is no single SPDX "
                              "license identifier")
