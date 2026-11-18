<!--
SPDX-License-Identifier: CC-BY-SA-4.0

Copyright (C) 2026 embedded brains GmbH & Co. KG
-->
# AGENTS.md

## Build and test

Run `make` before a commit. It regenerates the derived files, formats, analyses
`src/` and runs the tests. CI runs `make` and fails on any diff which it leaves
in the tree.

`pyproject.toml` makes `pytest` fail below 100 % line and branch coverage. Run
a single test with `--no-cov`:

```
uv run pytest --no-cov tests/test_itemmapper.py::test_item_mapper
```

Git tracks two generated files. Regenerate them with `make` after each edit of
`spec-types/spec/`.

| File | Generator |
| ---- | --------- |
| `src/specitems/spec.pickle` | `specpickle` from `spec-types/spec/*.yml` |
| `docs/source/items.rst` | `specdocitems` from `spec.pickle` |

## Item model

Each YAML file of a specification tree is one item. Its path below the tree
root gives the UID, such as `/spec/root`. `ItemCache` in `items.py` loads all
trees into one dictionary by UID.

The types are items themselves:

- A type item has `type: spec`. `spec-types/spec/root.yml` is the root type.
- A type links to its parent with the role `spec-refinement`. The link names a
  `spec-key` and a `spec-value`.
- `ItemTypeProvider.set_type()` follows the keys from the root. The type of an
  item is the path of the key values, such as `requirement/functional`.
- `specverify.py` checks each attribute against the `spec-info` of its type.
- `spec.pickle` freezes the types of this package. `spectypeview`, `specware`
  and `specmake` load it.

The other mechanisms which span several files:

| Mechanism | Where |
| --------- | ----- |
| `enabled-by` expressions over the enabled set | `is_enabled()`, `ItemSelection` |
| A `proxy` item resolves to a member item | `ItemCache.__missing__` |
| `${uid:/attribute}` substitution in item text | `itemmapper.py` |
| Output formats share the `Content` base | `content*.py` |

## Tests

Each `tests/spec-*/` directory is a fixture tree. `create_item_cache_config()`
in `tests/util.py` copies it into `tmpdir`. A log assertion compares the whole
log through `get_and_clear_log(caplog)`.

## Commits

A commit message follows Conventional Commits with a sentence-case subject. The
scope is the module name, or `spec` for `spec-types/`. Add the `Assisted-by:`
and `Signed-off-by:` trailers as `CONTRIBUTING.md` prescribes. Only a
maintainer runs `make publish` or `make devel-publish`.
