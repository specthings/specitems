# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the yamlroundtrip module. """

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

import pytest

from specitems import YAMLRoundTripError, yaml_round_trip

_TEXT_2_2_0 = """# comment
a: 'x'
b:
  c: "y"
  d:
  - e
  - f  # comment
"""

_TEXT_2_4_2 = """a: x
b:
  - c: y
    d: z
  - e
"""

_TEXT_4_4_0 = """a:
    b:
    -   c
"""

_TEXT_4_4_2 = """a:
    b:
      - c
"""


def _no_edit(_data):
    pass


@pytest.mark.parametrize(
    "text",
    [_TEXT_2_2_0, _TEXT_2_4_2, _TEXT_4_4_0, _TEXT_4_4_2, "---\na: b\n"])
def test_yaml_round_trip_unchanged(text):
    assert yaml_round_trip(text, _no_edit) == (text, True)


def _edit(data):
    data["b"]["d"].pop(0)
    data["b"]["c"] = "z"


def test_yaml_round_trip_change():
    assert yaml_round_trip(_TEXT_2_2_0, _edit) == ("""# comment
a: 'x'
b:
  c: "z"
  d:
  - f  # comment
""", True)


def test_yaml_round_trip_not_reproducible():
    with pytest.raises(YAMLRoundTripError,
                       match="does not reproduce the YAML text"):
        yaml_round_trip("a: b\n  c\n", _no_edit)
    with pytest.raises(YAMLRoundTripError,
                       match="does not reproduce the YAML text"):
        yaml_round_trip("a:   b\n", _no_edit)


def test_yaml_round_trip_not_exact():
    assert yaml_round_trip(
        "a:\n    b:\n      - c\n      - d\n    e: f\n      g\n",
        _no_edit,
        exact=False) == ("a:\n    b:\n      - c\n      - d\n    e: f g\n",
                         False)
    assert yaml_round_trip("a: b\n  c\n", _no_edit,
                           exact=False) == ("a: b c\n", False)


def test_yaml_round_trip_invalid():
    with pytest.raises(YAMLRoundTripError, match="cannot load the YAML text"):
        yaml_round_trip("a: [\n", _no_edit)
