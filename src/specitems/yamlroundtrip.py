# SPDX-License-Identifier: BSD-2-Clause
""" Provides a YAML round trip which keeps comments, order and quotes. """

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

import difflib
import io
from typing import Any, Callable

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

# Each entry is the mapping indent, the sequence indent and the sequence dash
# offset of a block style which the round trip tries in this order.
_INDENTS = ((2, 4, 2), (2, 2, 0), (4, 4, 0), (4, 4, 2))


class YAMLRoundTripError(ValueError):
    """ Indicates that a YAML text cannot go through a round trip. """


def _make_yaml(indent: tuple[int, int, int], explicit_start: bool) -> YAML:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.explicit_start = explicit_start
    yaml.indent(mapping=indent[0], sequence=indent[1], offset=indent[2])
    return yaml


def _dump(yaml: YAML, data: Any) -> str:
    stream = io.StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def yaml_round_trip(text: str,
                    edit: Callable[[Any], None],
                    exact: bool = True) -> tuple[str, bool]:
    """
    Load the YAML text, call edit with the data, and dump the data with the
    comments, the key order, the quotes and the indentation of the text.

    The indentation is the one whose dump of the unchanged data reproduces the
    text byte by byte.  If no indentation reproduces the text and exact is
    true, the function raises YAMLRoundTripError.  If exact is false, the dump
    uses the indentation whose dump of the unchanged data has the most lines
    in common with the text.

    Returns the dump and whether a dump of the unchanged data reproduces the
    text.
    """
    explicit_start = text.startswith("---")
    try:
        data = _make_yaml(_INDENTS[0], explicit_start).load(text)
    except YAMLError as err:
        raise YAMLRoundTripError(f"cannot load the YAML text: {err}") from err
    lines = text.splitlines()
    best_ratio = -1.0
    best_yaml = None
    for indent in _INDENTS:
        yaml = _make_yaml(indent, explicit_start)
        dump = _dump(yaml, data)
        if dump == text:
            edit(data)
            return _dump(yaml, data), True
        ratio = difflib.SequenceMatcher(None, lines, dump.splitlines()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_yaml = yaml
    if exact:
        raise YAMLRoundTripError(
            "a dump of the unchanged data does not reproduce the YAML text")
    assert best_yaml is not None
    edit(data)
    return _dump(best_yaml, data), False
