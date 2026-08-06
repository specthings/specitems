# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the clihash module. """

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

import os

from specitems.clihash import clihash


def _digest(capsys, argv: list[str]) -> str:
    clihash(argv)
    return capsys.readouterr().out.split()[1]


def test_clihash(capsys):
    path = os.path.join(os.path.dirname(__file__), "foobar.txt")
    whole = _digest(capsys, ["x", path])
    single = _digest(capsys, ["x", "--line=2", path])
    # A range without a last line covers exactly the begin line.
    assert _digest(capsys, ["x", "--line=2:2", path]) == single
    # The last line is included, so the range over all lines of a file without
    # a trailing newline yields the digest of the whole file.
    assert _digest(capsys, ["x", "--line=1:2", path]) == whole
    assert single != whole
    clihash(["x", "--algorithm=SHA256", "--format=hex", "--line=1:2", path])
