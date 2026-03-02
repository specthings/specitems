# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the cliutil module. """

# Copyright (C) 2025, 2026 embedded brains GmbH & Co. KG
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
import os
import logging

import pytest

from specitems.cliutil import (create_argument_parser, create_config,
                               init_logging, load_config)


@dataclasses.dataclass
class _Config:
    foo_bar: int = 1
    foobar: str = "?"
    default: int = 3


def test_create_config():
    obj = create_config({"foo-bar": 2, "foobar": "ups"}, _Config)
    assert isinstance(obj, _Config)
    assert obj.foo_bar == 2
    assert obj.foobar == "ups"
    assert obj.default == 3
    with pytest.raises(ValueError, match="has no attribute"):
        create_config({"nix": 0}, _Config)


def test_load_config():
    filename = os.path.join(os.path.dirname(__file__), "config", "a.yml")
    config = load_config(filename)
    assert config["a"] == "b"
    assert config["c"] == "d"


def test_create_argument_parser_default():
    parser = create_argument_parser()
    args = parser.parse_args([])
    assert args.log_level == "INFO"
    assert args.log_file is None
    assert not args.log_file_and_stderr


def test_init_logging_default(capfd):
    parser = create_argument_parser()
    args = parser.parse_args([])
    init_logging(args)
    logging.debug("debug")
    logging.info("info")
    logging.shutdown()
    captured = capfd.readouterr()
    assert captured.out == ""
    assert "debug" not in captured.err
    assert "info" in captured.err


def test_init_logging_file(tmpdir, capfd):
    parser = create_argument_parser()
    log_file = os.path.join(tmpdir, "log.txt")
    args = parser.parse_args([f"--log-file={log_file}"])
    assert args.log_file == log_file
    init_logging(args)
    logging.debug("debug")
    logging.info("info")
    logging.shutdown()
    captured = capfd.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    with open(log_file, "rb") as src:
        data = src.read()
        assert b"debug" not in data
        assert b"info" in data


def test_init_logging_file_and_stderr(tmpdir, capfd):
    parser = create_argument_parser()
    log_file = os.path.join(tmpdir, "log.txt")
    args = parser.parse_args(
        [f"--log-file={log_file}", "--log-file-and-stderr"])
    assert args.log_file == log_file
    init_logging(args)
    logging.debug("debug")
    logging.info("info")
    logging.shutdown()
    captured = capfd.readouterr()
    assert captured.out == ""
    assert "debug" not in captured.err
    assert "info" in captured.err
    with open(log_file, "rb") as src:
        data = src.read()
        assert b"debug" not in data
        assert b"info" in data
