# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the subprocessaction module. """

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

import dataclasses

from specitems.items import ItemCache, SpecTypeProvider
from specitems.specverify import verify_specification_format
from specitems.subprocessaction import run_subprocess_action
import specitems

from .util import create_item_cache_config, get_other_type_data_by_uid


@dataclasses.dataclass
class _Status():
    returncode: int


def test_subprocessaction(tmpdir, monkeypatch):
    config = create_item_cache_config(tmpdir, "spec-subprocessaction")
    type_provider = SpecTypeProvider(get_other_type_data_by_uid())
    item_cache = ItemCache(config, type_provider=type_provider)
    info = verify_specification_format(item_cache)
    assert info.critical == 0
    assert info.error == 0
    assert info.warning == 0
    assert info.info >= 0
    assert info.debug == 0

    commands: list[str] = []

    def _subprocess_run(cmd, env, check, cwd, stdout=None):
        commands.append(cmd[0])
        if cmd[0] == "file-not-found":
            raise FileNotFoundError("message")
        assert not check
        assert cmd[0] != "env" or env == {
            "FOO": "bar",
            "THE_PATH": "prepend:first:append"
        }
        assert cwd == "w"
        assert cmd[0] != "stdout" or stdout is not None
        return _Status(0)

    monkeypatch.setattr(specitems.subprocessaction.subprocess, "run",
                        _subprocess_run)
    uid = "/actions"
    for action in item_cache[uid]["actions"]:
        run_subprocess_action(uid, action)
    assert commands == ["env", "stdout", "file-not-found", "file-not-found"]
