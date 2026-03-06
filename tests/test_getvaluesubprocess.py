# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the getvaluesubprocess module. """

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

import functools
import os
import pytest
import subprocess

import specitems
from specitems.getvaluesubprocess import get_value_subprocess
from specitems.items import EmptyItem, ItemType
from specitems.itemmapper import ItemMapper


def _subprocess_run(args, stdin, stdout, stderr, shell, cwd, check, encoding):
    cp = subprocess.CompletedProcess(args, 0)
    if isinstance(args, list):
        args = " ".join(args)
    if args.startswith("no-output"):
        cp.stdout = None
    elif args.startswith("error"):
        raise subprocess.CalledProcessError(1, args)
    elif encoding is None:
        cp.stdout = b"no encoding"
    else:
        cp.stdout = str(args.encode(encoding))
    if not isinstance(stderr, int):
        stderr.write("\nstderr\n".encode("latin-1"))
    if not isinstance(stdout, int):
        stdout.write("\nstdout\n".encode("latin-1"))
    if not isinstance(stdin, int):
        assert isinstance(cp.stdout, bytes)
        cp.stdout += stdin.read()
    return cp


def _add_invisible(line) -> str:
    return "\u200b".join(char for char in line)


def _augment_report(lines):
    return lines, []


def test_getvaluesubprocess(monkeypatch, tmpdir):
    monkeypatch.setattr(specitems.getvaluesubprocess.subprocess, "run",
                        _subprocess_run)
    item = EmptyItem()
    item.cache.type_provider.root_type.refinements["foobar"] = ItemType(
        None, {})
    item.type = "foobar"
    item["SPDX-License-Identifier"] = "BSD-2-Clause"
    item["copyrights"] = ["Copyright (C) 2025 embedded brains GmbH & Co. KG"]
    item["dir"] = str(tmpdir)
    cwd = os.getcwd()
    item["cwd"] = cwd
    mapper = ItemMapper(item)
    mapper.add_get_value(
        "foobar:/subprocess",
        functools.partial(get_value_subprocess, mapper.substitute,
                          _augment_report))
    with pytest.raises(ValueError):
        mapper.substitute("${.:/subprocess:args=error}}")
    tmpdir_2 = _add_invisible(str(tmpdir))
    cwd_2 = _add_invisible(cwd)
    basename_2 = _add_invisible(os.path.basename(cwd))
    assert mapper.substitute("""${.:/subprocess:args=hide-cwd 1 2,hide_cwd=1}
${.:/subprocess:args=hide-output 3 4,strip_cwd=%(.:/cwd)/..,shell=0,hide_output=1}
${.:/subprocess:args=hide 5 6,hide=1,check=0}
${.:/subprocess:args=stderr,stderr=%(.:/dir)/stderr}
${.:/subprocess:args=stdout,stdout=%(.:/dir)/stdout}
${.:/subprocess:args=stdin stderr,stdin=%(.:/dir)/stderr}
${.:/subprocess:args=stdin stdout,stdin=%(.:/dir)/stdout}
${.:/subprocess:args=no-output,cwd=%(.:/dir),indent=1}
${.:/subprocess:args=a b c \\\\\\%\\(\\)\\0\\a\\b\\c\\f\\n\\r\\s\\t\\v,hidden_args=hidden,hide_args=1,encoding=latin-1}
${.:/subprocess:args=./%(.:/dir) --help,cwd=%(.:/dir),font-size=0}"""
                             ) == f""".. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​$​ ​h​i​d​e​-​c​w​d​ ​1​ ​2
    ​n​o​ ​e​n​c​o​d​i​n​g

.. raw:: latex

    \\end{{tiny}}
.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{basename_2}​ ​$​ ​h​i​d​e​-​o​u​t​p​u​t​ ​3​ ​4

.. raw:: latex

    \\end{{tiny}}

.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{cwd_2}​ ​$​ ​s​t​d​e​r​r
    ​n​o​ ​e​n​c​o​d​i​n​g

.. raw:: latex

    \\end{{tiny}}
.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{cwd_2}​ ​$​ ​s​t​d​o​u​t
    ​n​o​ ​e​n​c​o​d​i​n​g

.. raw:: latex

    \\end{{tiny}}
.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{cwd_2}​ ​$​ ​s​t​d​i​n​ ​s​t​d​e​r​r
    ​n​o​ ​e​n​c​o​d​i​n​g
    ​s​t​d​e​r​r

.. raw:: latex

    \\end{{tiny}}
.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{cwd_2}​ ​$​ ​s​t​d​i​n​ ​s​t​d​o​u​t
    ​n​o​ ​e​n​c​o​d​i​n​g
    ​s​t​d​o​u​t

.. raw:: latex

    \\end{{tiny}}
    .. raw:: latex

        \\begin{{tiny}}

    .. code-block:: none
        :linenos:
        :lineno-start: 1

        ​{tmpdir_2}​ ​$​ ​n​o​-​o​u​t​p​u​t

    .. raw:: latex

        \\end{{tiny}}
.. raw:: latex

    \\begin{{tiny}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​b​'​a​ ​h​i​d​d​e​n​ ​b​ ​c​ ​\\​\\​%​(​)​\\​x​0​0​\\​x​0​7​\\​x​0​8​,​\\​x​0​c​\\​n​\\​r​ ​\\​t​\\​x​0​b​'

.. raw:: latex

    \\end{{tiny}}
.. raw:: latex

    \\begin{{normalsize}}

.. code-block:: none
    :linenos:
    :lineno-start: 1

    ​{tmpdir_2}​ ​$​ ​.​/​{tmpdir_2}​ ​-​-​h​e​l​p
    ​n​o​ ​e​n​c​o​d​i​n​g

.. raw:: latex

    \\end{{normalsize}}"""
