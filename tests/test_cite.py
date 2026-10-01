# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the cite module. """

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

import os

import pytest

from specitems.cite import (BibTeXCitationProvider, get_reference_target,
                            get_reference_work, make_anchor, ReferenceTarget)
from specitems.contentsphinx import SphinxMapper
from specitems.items import Item, ItemCache, ItemCacheConfig, SpecTypeProvider
from specitems.specverify import verify_specification_format

_CITATIONS = ("article", "book", "booklet", "inbook", "incollection",
              "inproceedings", "manual", "mastersthesis", "misc", "phdthesis",
              "proceedings", "techreport")

_EXPECTED_BIBTEX_ENTRIES = """@article{RefArticle,
  author = {{Author In Book}},
  journal = {Journal In Book},
  month = {January},
  note = {Note In Book},
  number = {1 In Book},
  pages = {2 In Book},
  title = {{Article In Book}},
  volume = {3 In Book},
  year = {4 In Book},
}
@book{RefBook,
  author = {{Author}},
  date = {2026-09-07T14:30:00+08:00},
  edition = {1},
  editor = {{Editor}},
  month = {January},
  note = {Note},
  number = {2},
  publisher = {{Publisher}},
  series = {3},
  title = {{Book}},
  volume = {4},
  year = {5},
}
@booklet{RefBooklet,
  author = {{Author}},
  howpublished = {{How published}},
  month = {January},
  note = {Note},
  title = {{Booklet}},
  year = {1},
}
@inbook{RefInbook,
  author = {{Author}},
  chapter = {1},
  edition = {2},
  editor = {{Editor}},
  month = {January},
  note = {Note},
  number = {3},
  pages = {4},
  publisher = {{Publisher}},
  series = {5},
  title = {{In Book}},
  volume = {6},
  year = {7},
}
@incollection{RefIncollection,
  author = {{Author}},
  booktitle = {{Book}},
  chapter = {1},
  edition = {2},
  editor = {{Editor}},
  month = {January},
  note = {Note},
  number = {3},
  pages = {4},
  publisher = {{Publisher}},
  series = {5},
  title = {{In Collection}},
  volume = {6},
  year = {7},
}
@inproceedings{RefInproceedings,
  author = {{Author}},
  booktitle = {{Conference Proceedings}},
  editor = {{Editor A and Editor B}},
  month = {January},
  note = {Note},
  number = {1},
  organization = {{Organization}},
  pages = {2},
  publisher = {{Publisher}},
  series = {3},
  title = {{In Proceedings}},
  volume = {4},
  year = {5},
}
@manual{RefManual,
  author = {{Author}},
  edition = {1},
  month = {January},
  note = {Note},
  organization = {{Organization}},
  title = {{Manual}},
  year = {2},
}
@mastersthesis{RefMastersthesis,
  author = {{Author}},
  month = {January},
  note = {Note},
  school = {{School}},
  title = {{Masters Thesis}},
  year = {1},
}
@misc{RefMisc,
  author = {{A, B and C D, E}},
  date = {2026-09-07},
  howpublished = {{How published}},
  month = {January},
  note = {Note},
  title = {{Misc}},
  url = {https://foobar.org/doc_ument.pdf},
  year = {1},
}
@misc{RefOther,
  title = {{In Book}},
}
@phdthesis{RefPhdthesis,
  author = {{Author}},
  month = {January},
  note = {Note},
  school = {{School}},
  title = {{Ph.D. Thesis}},
  year = {1},
}
@proceedings{RefProceedings,
  editor = {{Editor}},
  month = {January},
  note = {Note},
  number = {1},
  organization = {{Organization}},
  publisher = {{Publisher}},
  series = {2},
  title = {{Conference Proceedings}},
  volume = {3},
  year = {4},
}
@techreport{RefTechreport,
  author = {{Author}},
  institution = {{Institution}},
  month = {January},
  note = {Note},
  number = {1},
  title = {{Techreport}},
  year = {2},
}
"""


def _get_fields(item: Item) -> tuple[str, dict[str, str]]:
    return "misc", {"title": item["name"]}


class _Provider(BibTeXCitationProvider):

    def __init__(self, mapper: SphinxMapper) -> None:
        super().__init__(mapper)
        self.add_get_fields("glossary", _get_fields)
        mapper.add_get_value("glossary:/cite-group", self.get_cite_group)


def test_cite(tmpdir):
    config = ItemCacheConfig(
        paths=[os.path.join(os.path.dirname(__file__), "spec-refs")],
        spec_type_root_uid="/spec/root",
        cache_directory=os.path.join(tmpdir, "cache"))
    cache = ItemCache(config, type_provider=SpecTypeProvider({}))
    info = verify_specification_format(cache)
    assert info.critical == 0
    assert info.error == 0
    assert info.warning == 0
    assert info.info >= 0
    assert info.debug == 0
    mapper = SphinxMapper(cache["/ref/article"], "CC-BY-SA-4.0")
    provider = _Provider(mapper)
    assert mapper.substitute("${/ref/other:/cite-group}") == ""
    assert mapper.substitute("${/ref/other:/cite-group:the-citation-group-key}"
                             ) == ":cite:`RefArticle` and :cite:`RefManual`"
    assert mapper.substitute("${.:/cite}") == ":cite:`RefArticle`"
    assert mapper.substitute(
        "${.:/cite-long}") == "*Article In Book* :cite:`RefArticle`"
    mapper.reset()
    content = mapper.create_content()
    provider.add_bibtex_entries(content)
    assert str(content) == ""
    for citation in _CITATIONS:
        assert mapper.substitute(
            f"${{/ref/{citation}:/cite}}"
        ) == f":cite:`Ref{citation[0].upper()}{citation[1:]}`"
    assert mapper.substitute("${/ref/other:/cite}") == f":cite:`RefOther`"
    provider.add_bibtex_entries(content)
    assert str(content) == _EXPECTED_BIBTEX_ENTRIES
    mapper.add_get_value("reference:/bibtex", provider.get_bibtex_entries)
    assert mapper.substitute("${.:/bibtex}") == _EXPECTED_BIBTEX_ENTRIES[:-1]


def test_reference_location(tmpdir):
    config = ItemCacheConfig(
        paths=[os.path.join(os.path.dirname(__file__), "spec-refs")],
        spec_type_root_uid="/spec/root",
        cache_directory=os.path.join(tmpdir, "cache"))
    cache = ItemCache(config, type_provider=SpecTypeProvider({}))
    assert make_anchor("SchedulerEDF") == "scheduleredf"
    assert make_anchor("internal_errors") == "internal-errors"
    assert make_anchor("_A  b_") == "a-b"
    web = cache["/ref/web"]
    area = cache["/ref/web/area"]
    user = cache["/ref/web/user"]
    assert get_reference_work(web) == web
    assert get_reference_work(area) == web
    with pytest.raises(ValueError, match="exactly one link"):
        get_reference_work(cache["/ref/web/orphan"])
    target = get_reference_target(web)
    assert target == ReferenceTarget(web, None, None, None, "", None,
                                     "https://foobar.org/doc")
    target = get_reference_target(area)
    assert target == ReferenceTarget(
        web, "Area", "Area_Label", "1.2", "/area.html", "area-label",
        "https://foobar.org/doc/area.html#area-label")
    links = list(user.links_to_parents("reference"))
    target = get_reference_target(links[0].item, links[0])
    assert target == ReferenceTarget(
        web, "Area", "Sub Label", "1.2.3", "/area.html/sub", "sub-label",
        "https://foobar.org/doc/area.html/sub#sub-label")
    target = get_reference_target(links[1].item, links[1])
    assert target == ReferenceTarget(web, None, None, None, "/page.html", None,
                                     "https://foobar.org/doc/page.html")
    nothing = cache["/ref/web/nothing"]
    target = get_reference_target(nothing, links[2])
    assert target == ReferenceTarget(cache["/ref/misc"], None, None, None, "",
                                     None, None)
    target = get_reference_target(links[3].item, links[3])
    assert target == ReferenceTarget(
        web, "Heading", "Heading_Label", None, "/heading.html", "the-heading",
        "https://foobar.org/doc/heading.html#the-heading")
    target = get_reference_target(links[4].item, links[4])
    assert target.label == "Area_Label"
    assert target.url == "https://foobar.org/doc/area.html#x-y"
    target = get_reference_target(links[5].item, links[5])
    assert target.label == "Other"
    assert target.url == "https://foobar.org/doc/heading.html#other"
    mapper = SphinxMapper(user, "CC-BY-SA-4.0")
    provider = BibTeXCitationProvider(mapper)
    assert mapper.substitute("${area:/cite}") == ":cite:`RefWeb`"
    assert mapper.substitute(
        "${area:/cite-long}") == "*Web*, Area :cite:`RefWeb`"
    assert mapper.substitute(
        "${nothing:/cite-long}") == "*Misc* :cite:`RefMisc`"
    assert mapper.substitute("${../web:/cite-long}") == (
        "*Web* :cite:`RefWeb`")
    content = mapper.create_content()
    provider.add_bibtex_entries(content)
    text = str(content)
    assert "@misc{RefWeb," in text
    assert "@misc{RefMisc," in text
    assert "Area" not in text
