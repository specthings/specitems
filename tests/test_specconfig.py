# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the specconfig module. """

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

import contextlib
import os
from pathlib import Path

import pytest

from specitems import (ContentContext, EmptyItemCache, Item, LicenseProvider,
                       SpecTypeProvider)
from specitems.specconfig import (CONFIG_FILE, check_license_items,
                                  create_content_context, create_type_provider,
                                  find_config_file, load_config_item,
                                  yield_tasks)

_CONFIG = """SPDX-License-Identifier: CC-BY-SA-4.0
copyrights:
- Copyright (C) 2026 embedded brains GmbH & Co. KG
enabled-by: true
item-cache:
  paths:
  - spec
links: []
tasks:
- task-name: verify
  task-type: spec-verification
  root-type: /spec/root
- task-name: other
  task-type: spec-verification
  root-type: /other/root
type: tool-config
"""


def _provider():
    return SpecTypeProvider({})


def test_find_config_file(tmp_path):
    assert find_config_file("x") == Path("x").absolute()
    with contextlib.chdir(tmp_path):
        with pytest.raises(FileNotFoundError, match=CONFIG_FILE):
            find_config_file()
        (tmp_path / CONFIG_FILE).write_text(_CONFIG, encoding="utf-8")
        os.makedirs(tmp_path / "a" / "b")
        with contextlib.chdir(tmp_path / "a" / "b"):
            assert find_config_file() == tmp_path / CONFIG_FILE


def test_load_config_item(tmp_path):
    path = tmp_path / CONFIG_FILE
    path.write_text(_CONFIG, encoding="utf-8")
    config = load_config_item(str(path))
    assert config["item-cache"]["paths"] == ["spec"]
    assert [
        task["task-name"] for task in yield_tasks(config, "spec-verification")
    ] == ["verify", "other"]
    assert not list(yield_tasks(config, "glossary"))


def test_load_config_item_invalid(tmp_path):
    path = tmp_path / CONFIG_FILE
    path.write_text(_CONFIG.replace("tasks:\n", "other:\n"), encoding="utf-8")
    with pytest.raises(ValueError, match="is invalid"):
        load_config_item(str(path), _provider())


def test_create_type_provider(monkeypatch):
    groups = []

    class _EntryPoint:

        def load(self):
            return dict

    def _entry_points(group):
        groups.append(group)
        return [_EntryPoint()]

    monkeypatch.setattr("importlib.metadata.entry_points", _entry_points)
    provider = create_type_provider()
    assert groups == ["specitems_type_provider.plugins"]
    assert provider.root_type_uid == "/spec/root"
    assert "/spec/root" in provider.data_by_uid


def test_create_content_context():
    context = create_content_context({
        "task-name":
        "code",
        "task-type":
        "interface",
        "license":
        "BSD-2-Clause",
        "accepted-licenses": ["MIT"],
        "automatically-generated-warning":
        "Do not edit.",
    })
    assert context.licenses.primary == "BSD-2-Clause"
    assert context.licenses.accepted == ["MIT"]
    assert context.licenses.name == "code"
    assert context.automatically_generated_warning == "Do not edit."
    assert context.provider is None
    context = create_content_context({
        "task-name": "doc",
        "task-type": "glossary",
        "license": "CC-BY-SA-4.0",
    })
    assert context.licenses.accepted == []
    assert context.automatically_generated_warning == ContentContext.DEFAULT_AUTOMATICALLY_GENERATED_WARNING


def test_create_content_context_prefix():
    task = {
        "task-name": "appl-config",
        "task-type": "appl-config",
        "doxygen-license": "BSD-2-Clause",
        "doxygen-accepted-licenses": ["MIT"],
        "documentation-license": "CC-BY-SA-4.0",
    }
    doxygen = create_content_context(task, prefix="doxygen-")
    assert doxygen.licenses.primary == "BSD-2-Clause"
    assert doxygen.licenses.accepted == ["MIT"]
    documentation = create_content_context(task, prefix="documentation-")
    assert documentation.licenses.primary == "CC-BY-SA-4.0"
    assert documentation.licenses.accepted == []


def _license_item(identifier):
    item = Item(
        EmptyItemCache(), f"/license/{identifier}", {
            "identifier": identifier,
            "name": identifier,
            "reproduce-text": False,
            "text": None,
            "uri": None,
        })
    item.type = "license"
    return item


def test_check_license_items():
    config = Item(
        EmptyItemCache(), "/config", {
            "tasks": [{
                "task-name": "a",
                "task-type": "appl-config",
                "doxygen-license": "BSD-2-Clause",
                "doxygen-accepted-licenses": ["MIT"],
                "documentation-license": "CC-BY-SA-4.0",
            }, {
                "task-name": "b",
                "task-type": "glossary",
                "license": "CC-BY-SA-4.0",
            }]
        })
    provider = LicenseProvider(
        [_license_item("BSD-2-Clause"),
         _license_item("CC-BY-SA-4.0")])
    with pytest.raises(ValueError) as err:
        check_license_items(config, provider)
    assert str(err.value) == ("no item states a license which the work a "
                              "may take: MIT")
    check_license_items(
        config,
        LicenseProvider([
            _license_item("BSD-2-Clause"),
            _license_item("CC-BY-SA-4.0"),
            _license_item("MIT")
        ]))
    config["tasks"][1]["license-by-target"] = [{
        "pattern": "a",
        "license": "CC-BY-SA-4.0"
    }]
    config["tasks"][1]["empty"] = []
    config["tasks"][1]["other"] = [{"pattern": "b"}]
    config["tasks"][0]["doxygen-accepted-licenses"] = []
    check_license_items(config, provider)
    config["tasks"][1]["license-by-target"].append({
        "pattern": "c",
        "license": "Apache-2.0"
    })
    with pytest.raises(ValueError) as err:
        check_license_items(config, provider)
    assert str(err.value) == ("no item states a license which the work b "
                              "may take: Apache-2.0")
    config["tasks"][0]["doxygen-accepted-licenses"] = ["MIT"]
    del config["tasks"][1]["license-by-target"]
    config["tasks"][1]["license"] = "Apache-2.0"
    with pytest.raises(ValueError) as err:
        check_license_items(config, provider)
    assert str(err.value) == ("no item states a license which the work a "
                              "may take: MIT\nno item states a license "
                              "which the work b may take: Apache-2.0")


def test_load_config_item_no_item(tmp_path):
    path = tmp_path / CONFIG_FILE
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="holds no item"):
        load_config_item(str(path))
