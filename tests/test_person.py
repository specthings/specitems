# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the person module. """

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

from specitems.items import ItemCache, ItemCacheConfig, SpecTypeProvider
from specitems.person import Person, get_affiliations


def test_person(tmpdir):
    config = ItemCacheConfig(
        paths=[os.path.join(os.path.dirname(__file__), "spec-refs-persons")],
        spec_type_root_uid="/spec/root",
        cache_directory=os.path.join(tmpdir, "cache"))
    cache = ItemCache(config, type_provider=SpecTypeProvider({}))
    erika = cache["/person/p0001"]
    georg = cache["/person/p0002"]
    some = cache["/organization/o0001"]
    other = cache["/organization/o0002"]
    person = Person(erika)
    assert person.item is erika
    assert person == Person(erika)
    assert len({person, Person(erika), Person(georg)}) == 2
    assert person.name == "Mustermann"
    assert person.first_name == "Erika"
    assert person.full_name == "Erika Mustermann"
    assert person.affiliations("2024") == [some]
    assert person.affiliations(None) == [other]
    reviewer = Person(cache["/person/p0003"])
    assert reviewer.first_name is None
    assert reviewer.full_name == "Reviewer A"
    assert reviewer.affiliations("2026") == []
    assert get_affiliations([erika], "2024") == [some]
    assert get_affiliations([erika], "2025-12-31") == [some]
    assert get_affiliations([erika], "2026-01-01") == [other]
    assert get_affiliations([erika], "2026") == [other]
    assert get_affiliations([erika], None) == [other]
    assert get_affiliations([georg, erika], "2024") == [some]
    assert get_affiliations([erika, georg], "2026") == [other, some]
    assert get_affiliations([], "2026") == []
