# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the licenseinfo module. """

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

import pytest

from specitems import EmptyItemCache, Item
from specitems.licenseinfo import LicenseAggregate, LicenseProvider


def test_primary_and_accepted():
    aggregate = LicenseAggregate("CC-BY-SA-4.0", ["Apache-2.0", "MIT"], "/d")
    assert aggregate.primary == "CC-BY-SA-4.0"
    assert aggregate.accepted == ["Apache-2.0", "MIT"]
    assert aggregate.name == "/d"
    assert not aggregate
    assert not aggregate.copyrights_of().get_statements()


def test_invalid_identifier():
    with pytest.raises(ValueError, match="no single SPDX license identifier"):
        LicenseAggregate("MIT OR BSD-2-Clause")
    with pytest.raises(ValueError, match="uses unknown identifiers: ECSS"):
        LicenseAggregate("MIT", ["ECSS"])


def test_select():
    aggregate = LicenseAggregate("CC-BY-SA-4.0", ["MIT", "Apache-2.0"])
    assert aggregate.select("CC-BY-SA-4.0 OR BSD-2-Clause") == "CC-BY-SA-4.0"
    assert aggregate.select("MIT OR Apache-2.0") == "MIT"
    assert aggregate.select("Apache-2.0") == "Apache-2.0"


def test_select_rejects():
    aggregate = LicenseAggregate("CC-BY-SA-4.0", ["MIT"], "/doc")
    with pytest.raises(ValueError) as err:
        aggregate.select("BSD-2-Clause", "/item")
    assert str(err.value) == (
        "the license expression 'BSD-2-Clause' of /item permits neither the "
        "primary license CC-BY-SA-4.0 of /doc nor an accepted license: MIT")
    aggregate = LicenseAggregate("CC-BY-SA-4.0")
    with pytest.raises(ValueError) as err:
        aggregate.select("BSD-2-Clause")
    assert str(err.value) == (
        "the license expression 'BSD-2-Clause' permits neither the primary "
        "license CC-BY-SA-4.0 nor an accepted license")


def test_register():
    aggregate = LicenseAggregate("CC-BY-SA-4.0", ["Apache-2.0"])
    assert aggregate.register("CC-BY-SA-4.0 OR BSD-2-Clause",
                              ["Copyright (C) 2020 A"], "/a") == "CC-BY-SA-4.0"
    assert aggregate.register("Apache-2.0", ["Copyright (C) 2021 B"],
                              "/b") == "Apache-2.0"
    assert aggregate.register("CC-BY-SA-4.0") == "CC-BY-SA-4.0"
    aggregate.register_copyrights(["Copyright (C) 2019 C"])
    entries = list(aggregate)
    assert [entry.the_license
            for entry in entries] == ["Apache-2.0", "CC-BY-SA-4.0"]
    assert entries[0].expressions == {"Apache-2.0"}
    assert entries[0].provenance == {"/b"}
    assert entries[0].copyrights.get_statements() == ["Copyright (C) 2021 B"]
    assert entries[1].expressions == {
        "CC-BY-SA-4.0", "CC-BY-SA-4.0 OR BSD-2-Clause"
    }
    assert entries[1].provenance == {"/a"}
    assert aggregate.copyrights_of().get_statements() == [
        "Copyright (C) 2020 A", "Copyright (C) 2019 C"
    ]
    assert aggregate.copyrights_of("Apache-2.0").get_statements() == [
        "Copyright (C) 2021 B"
    ]
    assert [entry.the_license
            for entry in aggregate.foreign()] == ["Apache-2.0"]
    assert bool(aggregate)


def _license_item(uid, identifier, reproduce=False, text=None, uri=None):
    item = Item(
        EmptyItemCache(), uid, {
            "identifier": identifier,
            "name": f"The {identifier} License",
            "reproduce-text": reproduce,
            "text": text,
            "uri": uri,
        })
    item.type = "license"
    return item


def test_provider():
    other = Item(EmptyItemCache(), "/other", {})
    other.type = "spec"
    provider = LicenseProvider([
        other,
        _license_item("/l/mit", "MIT", True, "The MIT text"),
        _license_item("/l/cc", "CC-BY-SA-4.0", False, None,
                      "https://example.org/cc"),
    ])
    assert "MIT" in provider
    assert "Apache-2.0" not in provider
    assert provider.name_of("MIT") == "The MIT License"
    assert provider.text_of("MIT") == "The MIT text"
    assert provider.text_of("CC-BY-SA-4.0") is None
    assert provider.uri_of("CC-BY-SA-4.0") == "https://example.org/cc"
    assert provider.uri_of("MIT") is None
    with pytest.raises(ValueError,
                       match="no item states the license Apache-2.0"):
        provider.name_of("Apache-2.0")


def test_provider_errors():
    with pytest.raises(ValueError) as err:
        LicenseProvider(
            [_license_item("/a", "MIT"),
             _license_item("/b", "MIT")])
    assert str(err.value) == "the items /a and /b state the license MIT"
    with pytest.raises(ValueError) as err:
        LicenseProvider([_license_item("/c", "MIT", True)])
    assert str(err.value) == ("the item /c reproduces the text of the license "
                              "MIT and carries none")
