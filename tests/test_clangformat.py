# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the clangformat module. """

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

import dataclasses
import subprocess

import pytest
import specitems
from specitems import ClangFormatter


@dataclasses.dataclass
class _Status():
    stdout: str


def test_clang_formatter_attributes():
    formatter = ClangFormatter("foo", "bar")
    assert formatter.path == "foo"
    assert formatter.style == "bar"


def test_check_available(monkeypatch):
    calls = []

    def _subprocess_run(cmd, capture_output, encoding, check):
        calls.append(cmd)
        assert capture_output
        assert encoding == "utf-8"
        assert check
        return _Status("clang-format version 21.1.0")

    monkeypatch.setattr(specitems.clangformat.subprocess, "run",
                        _subprocess_run)

    ClangFormatter("foo", "bar").check_available()
    assert calls == [["foo", "--version"]]


def test_check_available_error(monkeypatch):

    def _subprocess_run(cmd, capture_output, encoding, check):
        raise FileNotFoundError(cmd[0])

    monkeypatch.setattr(specitems.clangformat.subprocess, "run",
                        _subprocess_run)

    with pytest.raises(FileNotFoundError):
        ClangFormatter("foo", "bar").check_available()


def test_format_text(monkeypatch):
    calls = []

    def _subprocess_run(cmd, input, capture_output, encoding, check):
        calls.append((cmd, input))
        assert capture_output
        assert encoding == "utf-8"
        assert check
        return _Status("int a;\n")

    monkeypatch.setattr(specitems.clangformat.subprocess, "run",
                        _subprocess_run)

    formatter = ClangFormatter("foo", "file")
    assert formatter.format_text("int  a;\n", "a/b/c.h") == "int a;\n"
    assert calls == [([
        "foo",
        "--style=file",
        "--assume-filename=a/b/c.h",
    ], "int  a;\n")]


def test_format_text_error(monkeypatch):

    def _subprocess_run(cmd, input, capture_output, encoding, check):
        raise subprocess.CalledProcessError(1, cmd, stderr="bad style")

    monkeypatch.setattr(specitems.clangformat.subprocess, "run",
                        _subprocess_run)

    with pytest.raises(subprocess.CalledProcessError):
        ClangFormatter("foo", "bar").format_text("int a;\n", "c.h")
