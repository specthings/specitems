# SPDX-License-Identifier: BSD-2-Clause
""" Provides the configuration item of a tree. """

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

import logging
from pathlib import Path
from typing import Any, Iterator, Optional

from .cliutil import load_config
from .content import ContentContext
from .licenseinfo import LicenseAggregate, LicenseProvider
from .items import (EmptyItemCache, Item, ItemDataByUID, ItemTypeProvider,
                    SpecTypeProvider)
from .specverify import SpecVerifier

#: The name of the configuration file of a tree.
CONFIG_FILE = "specitems.yml"

#: The UID of the configuration item.
CONFIG_UID = "/config"


def find_config_file(config_file: Optional[str] = None) -> Path:
    """
    Find the configuration file of the tree.

    Args:
        config_file: The path to the configuration file.  None searches the
            current directory and its parent directories.

    Returns:
        The absolute path to the configuration file.

    Raises:
        FileNotFoundError: The search found no configuration file.
    """
    if config_file is not None:
        return Path(config_file).absolute()
    base = Path(".").absolute()
    while True:
        path = base / CONFIG_FILE
        if path.is_file():
            return path
        parent = base.parent
        if parent == base:
            raise FileNotFoundError(
                f"cannot find file {CONFIG_FILE} in the current directory or "
                "its parent directories")
        base = parent


def load_config_item(config_file: Optional[str] = None,
                     type_provider: Optional[ItemTypeProvider] = None) -> Item:
    """
    Load the configuration item of the tree and verify it.

    The item defines the item cache of the tree, so it loads into a cache of
    its own.  The types come from the installed packages.

    Args:
        config_file: The path to the configuration file.  None searches the
            current directory and its parent directories.
        type_provider: The provider of the specification types.  None takes
            the types of the installed packages.

    Returns:
        The configuration item.

    Raises:
        FileNotFoundError: The search found no configuration file.
        ValueError: The configuration item is invalid.
    """
    path = find_config_file(config_file)
    if type_provider is None:
        type_provider = create_type_provider()
    data = load_config(str(path))
    if not isinstance(data, dict):
        raise ValueError(f"the configuration file {path} holds no item")
    item_cache = EmptyItemCache(type_provider=type_provider)
    item = item_cache.add_item(CONFIG_UID, data)
    root_type_uid = item_cache.type_provider.root_type_uid
    # The item defines the item cache of the tree, so no tree exists yet and
    # no UID of the item resolves.
    verifier = SpecVerifier(item_cache, root_type_uid or "", logging.INFO)
    status = verifier.verify(item)
    if status.error or status.critical:
        raise ValueError(f"the configuration file {path} is invalid")
    logging.info("use configuration file %s", path)
    return item


def create_type_provider() -> ItemTypeProvider:
    """
    Create the provider of the specification types of the installed packages.

    A package registers its types through the entry point group
    ``specitems_type_provider.plugins``.

    Returns:
        The type provider.
    """
    # The import is local, so a caller which provides its own types pays not
    # for the entry point lookup.
    import importlib.metadata  # pylint: disable=import-outside-toplevel
    data_by_uid: ItemDataByUID = {}
    for entry_point in importlib.metadata.entry_points(
            group="specitems_type_provider.plugins"):
        data_by_uid.update(entry_point.load()())
    return SpecTypeProvider(data_by_uid)


def create_content_context(task: dict,
                           provider: Optional[LicenseProvider] = None,
                           prefix: str = "") -> ContentContext:
    """
    Create the content context of the task.

    A task which produces files of two kinds states the license of each kind
    under a prefix of its own.

    Args:
        task: The task of a tool.  It states the license of the files which it
            produces, the licenses which they accept, and the warning which
            they carry.
        provider: The presentation of the licenses of the tree.
        prefix: The prefix of the license attributes of the task.

    Returns:
        The content context.

    Raises:
        ValueError: A license of the task is invalid.
    """
    return ContentContext(
        LicenseAggregate(task[f"{prefix}license"],
                         task.get(f"{prefix}accepted-licenses", []),
                         task["task-name"]),
        task.get("automatically-generated-warning", None), provider)


def _is_license_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(record, dict) and "license" in record for record in value)


def check_license_items(config: Item, provider: LicenseProvider) -> None:
    """
    Check that the tree states every license which a task may produce.

    A task attribute which ends in ``license`` states a license of the task.
    Its prefix is the prefix of :func:`create_content_context`.  A task
    attribute which is a list of mappings with a ``license`` key states the
    license of some files of the task in each mapping.

    Args:
        config: The configuration item.
        provider: The presentation of the licenses of the tree.

    Raises:
        ValueError: No item states a license which a task may produce.
    """
    errors: list[str] = []
    for task in config["tasks"]:
        contexts: list[ContentContext] = []
        for key, value in sorted(task.items()):
            if key.endswith("license"):
                contexts.append(
                    create_content_context(task, provider,
                                           key[:-len("license")]))
            elif _is_license_list(value):
                contexts.extend(
                    ContentContext(
                        LicenseAggregate(record["license"], [],
                                         task["task-name"]), None, provider)
                    for record in value)
        for context in contexts:
            try:
                context.check_license_items()
            except ValueError as err:
                errors.append(str(err))
    if errors:
        raise ValueError("\n".join(errors))


def yield_tasks(config: Item, task_type: str) -> Iterator[dict]:
    """
    Yield the tasks of the type in the order of the configuration.

    Args:
        config: The configuration item.
        task_type: The type of the tasks.

    Yields:
        Every task of the type.
    """
    for task in config["tasks"]:
        if task["task-type"] == task_type:
            yield task
