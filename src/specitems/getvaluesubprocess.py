# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a function to get an item value substitution by means of running a
subprocess.
"""

# Copyright (C) 2019, 2025 embedded brains GmbH & Co. KG
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
import logging
import os
import subprocess
from typing import Any, BinaryIO, Callable

from .itemmapper import ItemGetValueContext, unpack_arg
from .contentsphinx import SphinxContent

_Substitute = Callable[[str], str]
_AugmentReport = Callable[[list[str]], tuple[list[str], list[tuple[int, int]]]]


@dataclasses.dataclass
class _Subprocess:
    # pylint: disable=too-many-instance-attributes
    args: str | list[str] = ""
    encoding: None | str = None
    check: bool = True
    cwd: str = "."
    hide: bool = False
    hide_args: bool = False
    hide_cwd: bool = False
    hide_output: bool = False
    hidden_args: list[str] = dataclasses.field(default_factory=list)
    indent: int = 0
    font_size: int = -4
    shell: bool = True
    stderr: int | BinaryIO = subprocess.STDOUT
    stdin: int | BinaryIO = subprocess.DEVNULL
    stdout: int | BinaryIO = subprocess.PIPE
    strip_cwd: str = ""

    def __enter__(self) -> "_Subprocess":
        return self

    def __exit__(self, *args, **kwargs) -> None:
        if not isinstance(self.stderr, int):
            self.stderr.close()
        if not isinstance(self.stdin, int):
            self.stdin.close()
        if not isinstance(self.stdout, int):
            self.stdout.close()


def _subprocess_escape(arg: str, substitute: _Substitute) -> str:
    return substitute(unpack_arg(arg))


def _parse_subprocess_args(ctx: ItemGetValueContext, substitute: _Substitute,
                           process: _Subprocess) -> None:
    assert ctx.args
    process.cwd = _subprocess_escape(process.cwd, substitute)
    for arg in ctx.args.split(","):
        name, _, value = arg.partition("=")
        name = name.replace("-", "_")
        if name in ("args", "hidden_args"):
            value_2: Any = [
                _subprocess_escape(arg_2, substitute)
                for arg_2 in value.split(" ")
            ]
        else:
            # pylint: disable=consider-using-with
            value_2 = _subprocess_escape(value, substitute)
            if isinstance(getattr(process, name), bool):
                value_2 = bool(int(value_2))
            elif name in ("indent", "font_size"):
                value_2 = int(value_2)
            elif name in "stdin":
                value_2 = open(value_2, "rb")
            elif name in ("stderr", "stdout"):
                value_2 = open(value_2, "wb")
        setattr(process, name, value_2)


def get_value_subprocess(substitute: _Substitute,
                         augment_report: _AugmentReport,
                         ctx: ItemGetValueContext) -> str:
    """ Get a value from a subprocess. """
    with _Subprocess() as process:
        _parse_subprocess_args(ctx, substitute, process)
        cwd = os.path.normpath(os.path.abspath(process.cwd))
        args = [process.args[0]]
        args.extend(process.hidden_args)
        args.extend(process.args[1:])
        logging.info("run in '%s': %s", cwd,
                     " ".join(f"'{arg}'" for arg in args))
        try:
            result = subprocess.run(" ".join(args) if process.shell else args,
                                    stdin=process.stdin,
                                    stdout=process.stdout,
                                    stderr=process.stderr,
                                    shell=process.shell,
                                    cwd=cwd,
                                    check=process.check,
                                    encoding=process.encoding)
        except subprocess.CalledProcessError as err:
            logging.error("subprocess failed with stdout '%s' and stderr '%s'",
                          err.stdout, err.stderr)
            raise err
        if process.hide:
            return ""
        content = SphinxContent()
        with content.indent(levels=process.indent):
            lines: list[str] = []
            if not process.hide_args:
                if process.hide_cwd:
                    cwd = ""
                elif process.strip_cwd:
                    strip = f"{os.path.normpath(process.strip_cwd)}/"
                    cwd = f"{cwd.removeprefix(strip)} "
                else:
                    cwd = f"{cwd} "
                lines.append(f"{cwd}$ {' '.join(process.args)}")
            if not process.hide_output and result.stdout:
                if process.encoding is None:
                    stdout = result.stdout.decode("latin-1")
                else:
                    stdout = result.stdout
                assert isinstance(stdout, str)
                lines.extend(stdout.rstrip("\r\n").split("\n"))
            lines, data_ranges = augment_report(lines)
            content.add_program_output(lines,
                                       data_ranges,
                                       font_size=process.font_size)
        return content.join()
