# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the clitypeview module. """

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

import specitems.clitypeview
from specitems.clitypeview import clitypeview

# A small, self-contained substitute for the real (large) bundled
# specitems type system plus two fake plugin packages, used instead of the
# real data so tests do not depend on it and can exercise every branch
# (duplicate refinement links, redefined UIDs, ambiguous/unknown lookups,
# an unrelated excluded package, ...).


def _type(spec_type, spec_name, spec_info, links=()):
    return {
        "type": "spec",
        "enabled-by": True,
        "links": list(links),
        "spec-name": spec_name,
        "spec-type": spec_type,
        "spec-info": spec_info,
        "spec-description": None,
        "spec-example": None,
    }


def _refines(parent_uid, key, value):
    return {
        "role": "spec-refinement",
        "spec-key": key,
        "spec-value": value,
        "uid": parent_uid
    }


_SPECITEMS_DATA = {
    "/spec/root": _type("root", "Root Item Type", {"dict": {}}),
    "/spec/name": _type("name", "Name", {"str": {}}),
}

_WIDGET_DATA = {
    "/spec/widget":
    _type("widget", "Widget Item Type", {"dict": {}},
          [_refines("/spec/root", "type", "widget")]),
    # refines the same parent through two links -- must be listed once
    "/spec/widget-a":
    _type("widget-variant", "Widget A", {"dict": {}}, [
        _refines("/spec/widget", "color", "red"),
        _refines("/spec/widget", "color", "teal"),
    ]),
    "/spec/widget-b":
    _type("widget-variant", "Widget B", {"dict": {}},
          [_refines("/spec/widget", "color", "blue")]),
    "/spec/widget-color":
    _type("widget-color", "Widget Color", {"str": {}}),
    "/spec/gizmo":
    _type("gizmo-kind", "Gizmo", {
        "bool": {},
        "list": {}
    }),
    # a member with its own sub-hierarchy: "paint" never chains back to
    # root, but "paint-glossy" refines it -- that nesting must survive
    "/spec/paint":
    _type("paint", "Paint", {"str": {}}),
    "/spec/paint-glossy":
    _type("paint-glossy", "Glossy Paint", {"str": {}},
          [_refines("/spec/paint", "finish", "glossy")]),
}

_GADGET_DATA = {
    "/spec/gadget":
    _type("gadget", "Gadget Item Type", {"dict": {}},
          [_refines("/spec/root", "type", "gadget")]),
    # redefines a UID from fakepluginone with different content
    "/spec/widget":
    _type("widget", "Widget Item Type (v2)", {
        "dict": {},
        "list": {}
    }, [_refines("/spec/root", "type", "widget")]),
    # redefines a UID from fakepluginone with identical content
    "/spec/widget-color":
    _WIDGET_DATA["/spec/widget-color"],
    # refines a type from a package excluded by --package: no root to
    # nest it under in that case, so it must still show up, flat
    "/spec/orphan-child":
    _type("orphan-child", "Orphan Child", {"dict": {}},
          [_refines("/spec/unrelated", "kind", "child")]),
}

_UNRELATED_DATA = {
    "/spec/unrelated":
    _type("unrelated", "Unrelated Item Type", {"dict": {}},
          [_refines("/spec/root", "type", "unrelated")]),
}


class _FakeEntryPoint:

    def __init__(self, module, data):
        self.module = module
        self._data = data

    def load(self):
        return lambda: self._data


def _install_fakes(monkeypatch,
                   entry_points=(),
                   specitems_data=None,
                   requires=None,
                   width=100):
    monkeypatch.setattr(
        specitems.clitypeview, "pickle_load_data_by_uid",
        lambda _path: specitems_data
        if specitems_data is not None else dict(_SPECITEMS_DATA))
    monkeypatch.setattr(specitems.clitypeview.importlib.metadata,
                        "entry_points", lambda group: list(entry_points))
    if requires is not None:
        monkeypatch.setattr(specitems.clitypeview.importlib.metadata,
                            "requires", requires)
    monkeypatch.setattr(specitems.clitypeview, "_effective_width",
                        lambda: width)


def _default_entry_points():
    return [
        _FakeEntryPoint("fakepluginone.plugin", dict(_WIDGET_DATA)),
        _FakeEntryPoint("fakeplugintwo.plugin", dict(_GADGET_DATA)),
        _FakeEntryPoint("fakeplugin3.plugin", dict(_UNRELATED_DATA)),
    ]


def test_effective_width():
    assert specitems.clitypeview._effective_width() >= 1


def test_defining_file():
    assert specitems.clitypeview._defining_file("/spec/build") == "build.yml"
    # defensive fallback for a uid outside the /spec/ namespace, should
    # one ever occur -- shown as-is rather than mangled
    assert specitems.clitypeview._defining_file(
        "/other/build") == "/other/build.yml"


def test_tree(monkeypatch, capsys):
    _install_fakes(monkeypatch, _default_entry_points())
    assert clitypeview(["x"]) is None
    out, err = capsys.readouterr()
    assert "warning: 'fakeplugintwo' redefines the type from 'widget.yml' " \
        "already provided by 'fakepluginone' (with different content); " \
        "using the 'fakeplugintwo' definition" in err
    assert "redefines the type from 'widget-color.yml'" in err
    assert "with different content" not in err.split("widget-color.yml",
                                                     1)[1].split("\n", 1)[0]
    lines = out.splitlines()
    assert lines[0] == "root.yml (specitems) {dict} Root Item Type"
    # the file a type is defined in, not its uid -- and no redundant
    # "/spec/" (it is on every single line, so it carries no information)
    assert not any("/spec/" in line for line in lines)
    assert any(
        line.endswith("[type=widget] widget.yml (fakeplugintwo) {dict|list} "
                      "Widget Item Type (v2)") for line in lines)
    # duplicate spec-refinement links to the same parent collapse to one
    # entry, with all of its values shown
    assert sum("widget-a.yml" in line for line in lines) == 1
    assert any("[color=red|teal] widget-a.yml" in line for line in lines)
    # members are their own forest, not nested under the root
    assert "Types not reachable from the root type via spec-refinement:" \
        in out
    assert "- name.yml (specitems) {str} Name" in out
    assert "- gizmo.yml (fakepluginone) {bool|list} Gizmo" in out
    # ... but a member's own refinements are still nested underneath it
    paint_index = next(i for i, line in enumerate(lines)
                       if line.startswith("- paint.yml "))
    assert lines[paint_index + 1].endswith(
        "paint-glossy.yml (fakepluginone) {str} Glossy Paint")


def test_package_filter(monkeypatch, capsys):

    def _requires(package):
        return {
            # "not-a-known-package" is well-formed but irrelevant, and the
            # leading space makes " !not-a-requirement" match nothing --
            # both are ignored
            "fakeplugintwo": [
                "fakepluginone>=1", "not-a-known-package>=2",
                " !not-a-requirement"
            ],
            "fakepluginone": ["specitems>=1"],
        }.get(package, [])

    _install_fakes(monkeypatch, [
        _FakeEntryPoint("fakepluginone.plugin", dict(_WIDGET_DATA)),
        _FakeEntryPoint("fakeplugintwo.plugin", dict(_GADGET_DATA)),
        _FakeEntryPoint("fakeplugin3.plugin", dict(_UNRELATED_DATA)),
    ],
                   requires=_requires)
    assert clitypeview(["x", "--package", "fakeplugintwo"]) is None
    out, _ = capsys.readouterr()
    assert "gadget.yml" in out
    assert "widget.yml" in out
    assert "unrelated.yml" not in out
    # orphan-child refines "/spec/unrelated", excluded by the package
    # filter -- there is no root left to nest it under, so it is still
    # shown, just flat
    assert "- orphan-child.yml (fakeplugintwo) {dict} Orphan Child" in out


def test_unknown_package(monkeypatch, capsys):
    _install_fakes(monkeypatch)
    assert clitypeview(["x", "--package", "doesnotexist"]) == 1
    _, err = capsys.readouterr()
    assert "unknown package 'doesnotexist'" in err
    assert "specitems" in err


def test_missing_root(monkeypatch, capsys):
    _install_fakes(monkeypatch, specitems_data={})
    assert clitypeview(["x"]) == 1
    _, err = capsys.readouterr()
    assert "the root type '/spec/root' was not found" in err


def test_no_leftover_value_types(monkeypatch, capsys):
    # every loaded type is reachable from root -- nothing left for the
    # separate value-types section
    _install_fakes(monkeypatch,
                   specitems_data={
                       "/spec/root": _type("root", "Root Item Type",
                                           {"dict": {}})
                   })
    assert clitypeview(["x"]) is None
    out, _ = capsys.readouterr()
    assert "Types not reachable from the root type" not in out


def test_ancestors_by_uid_and_short_uid(monkeypatch, capsys):
    _install_fakes(monkeypatch, _default_entry_points())
    assert clitypeview(["x", "--ancestors", "/spec/widget"]) is None
    by_uid, _ = capsys.readouterr()
    assert clitypeview(["x", "--ancestors", "widget"]) is None
    by_short_uid, _ = capsys.readouterr()
    assert clitypeview(["x", "--ancestors", "widget.yml"]) is None
    by_file_name, _ = capsys.readouterr()
    assert by_uid == by_short_uid == by_file_name
    assert by_uid.splitlines() == [
        "root.yml (specitems) {dict} Root Item Type",
        "    └── [type=widget] widget.yml (fakeplugintwo) {dict|list} "
        "Widget Item Type (v2)",
    ]


def test_ancestors_by_unique_spec_type(monkeypatch, capsys):
    _install_fakes(monkeypatch, _default_entry_points())
    assert clitypeview(["x", "--ancestors", "gizmo-kind"]) is None
    out, _ = capsys.readouterr()
    assert out.splitlines() == [
        "gizmo.yml (fakepluginone) {bool|list} Gizmo",
    ]


def test_ancestors_ambiguous(monkeypatch):
    _install_fakes(monkeypatch, _default_entry_points())
    with pytest.raises(SystemExit, match="ambiguous type name"):
        clitypeview(["x", "--ancestors", "widget-variant"])


def test_ancestors_not_found(monkeypatch):
    _install_fakes(monkeypatch, _default_entry_points())
    with pytest.raises(SystemExit, match="no type named or UID'd"):
        clitypeview(["x", "--ancestors", "does-not-exist"])


def test_wrapping(monkeypatch, capsys):
    long_name = "A Very Long Descriptive Name Used To Force Line Wrapping"
    _install_fakes(monkeypatch,
                   specitems_data={
                       "/spec/root": _type("root", "Root Item Type",
                                           {"dict": {}}),
                       "/spec/wrap-me": _type("wrap-me", long_name,
                                              {"str": {}}),
                   },
                   width=30)
    assert clitypeview(["x"]) is None
    out, _ = capsys.readouterr()
    lines = [
        line for line in out.splitlines()
        if line and "Types not reachable from the root type" not in line
    ]
    assert all(len(line) <= 30 for line in lines)
    assert any("Descriptive" in line for line in lines)


def test_bracket_wrapping(monkeypatch, capsys):
    # modeled on pkg-sphinx-types, which refines pkg-sphinx-document once
    # per document-type value it stands in for -- none of that is
    # conveyed by its own uid, so the [key=value] bracket must survive
    # and, if long, wrap without splitting a value across lines
    document_types = [
        "ddf-sreld", "djf-svr", "package-manual", "test-plan", "ts-icd",
        "ts-srs", "generic"
    ]
    _install_fakes(monkeypatch,
                   specitems_data={
                       "/spec/root":
                       _type("root", "Root Item Type", {"dict": {}}),
                       "/spec/doc":
                       _type("doc", "Document", {"dict": {}}),
                       "/spec/doc-types":
                       _type("doc-types", "Generic Document Types",
                             {"dict": {}}, [
                                 _refines("/spec/doc", "document-type", value)
                                 for value in document_types
                             ]),
                   },
                   width=40)
    assert clitypeview(["x"]) is None
    out, _ = capsys.readouterr()
    lines = [
        line for line in out.splitlines()
        if line and "Types not reachable from the root type" not in line
    ]
    assert all(len(line) <= 40 for line in lines)
    bracket_lines = "".join(
        line.strip() for line in lines if "document-type=" in line
        or line.strip().startswith("|") or line.strip().endswith("]"))
    for value in document_types:
        assert f"|{value}" in bracket_lines or f"={value}" in bracket_lines
