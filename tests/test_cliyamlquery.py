# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the cliyamlquery module. """

# Copyright (C) 2025 embedded brains GmbH & Co. KG
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

import ast
import os

from specitems.cliyamlquery import cliyamlquery

_C_YML = os.path.join(os.path.dirname(__file__), "spec-item-cache", "c.yml")


def test_cliyamlquery(capsys):
    cliyamlquery(["x", "/v", _C_YML])
    captured = capsys.readouterr()
    assert captured.out == f"c{os.linesep}"
    cliyamlquery(["x", "/r", _C_YML])
    captured = capsys.readouterr()
    assert captured.out == f"${{.:/s}}{os.linesep}"


def test_cliyamlquery_substitute(capsys):
    cliyamlquery(["x", "--substitute", "/r", _C_YML])
    captured = capsys.readouterr()
    assert captured.out == f"c{os.linesep}"


def test_cliyamlquery_substitute_item(capsys):
    cliyamlquery(["x", "--substitute", "/", _C_YML])
    captured = capsys.readouterr()
    assert ast.literal_eval(captured.out)["r"] == "c"
