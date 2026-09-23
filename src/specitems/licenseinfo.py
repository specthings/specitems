# SPDX-License-Identifier: BSD-2-Clause
""" Provides the aggregated license and copyright information of a work. """

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

from typing import Iterable, Iterator, Optional, Sequence

from .copyrights import Copyrights
from .items import Item
from .spdx import parse_license_identifier, permits


class LicenseEntry:
    """
    Holds the copyrights of the parts of a work which take one license.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, the_license: str) -> None:
        self.the_license = the_license
        self.copyrights = Copyrights()
        self.expressions: set[str] = set()
        self.provenance: set[str] = set()

    def __lt__(self, other: "LicenseEntry") -> bool:
        return self.the_license < other.the_license


class LicenseAggregate:
    """
    Holds the license and copyright information of one work.

    A work takes one primary license.  A part of the work which the primary
    license does not permit keeps its own license, which the work accepts
    only where the configuration names it.  The work lists the copyrights of
    such a part, and the list may sit outside the work.
    """

    def __init__(self,
                 primary: str,
                 accepted: Sequence[str] = (),
                 name: str = "") -> None:
        """
        Initialize the aggregate.

        Args:
            primary: The primary SPDX license identifier of the work.
            accepted: The SPDX license identifiers of the foreign licenses
                which the work accepts, in the order of their preference.
            name: The name of the work, used by the error messages.

        Raises:
            ValueError: An identifier is no single SPDX license identifier.
        """
        self._primary = parse_license_identifier(primary)
        self._accepted = [
            parse_license_identifier(the_license) for the_license in accepted
        ]
        self._name = name
        self._entries: dict[str, LicenseEntry] = {}

    @property
    def primary(self) -> str:
        """ Is the primary license of the work. """
        return self._primary

    @property
    def accepted(self) -> Sequence[str]:
        """ Are the foreign licenses which the work accepts. """
        return self._accepted

    @property
    def name(self) -> str:
        """ Is the name of the work. """
        return self._name

    def select(self, expression: str, provenance: str = "") -> str:
        """
        Select the license under which the work takes the part.

        Args:
            expression: The SPDX license expression of the part.
            provenance: The origin of the part, used by the error messages.

        Returns:
            The primary license where the expression permits it, otherwise the
            first accepted license which the expression permits.

        Raises:
            ValueError: The expression is invalid, or it permits neither the
                primary license nor an accepted license.
        """
        if permits(expression, self._primary):
            return self._primary
        for the_license in self._accepted:
            if permits(expression, the_license):
                return the_license
        where = f" of {provenance}" if provenance else ""
        work = f" of {self._name}" if self._name else ""
        accepted = ""
        if self._accepted:
            accepted = f": {', '.join(self._accepted)}"
        raise ValueError(
            f"the license expression '{expression}'{where} permits neither "
            f"the primary license {self._primary}{work} nor an accepted "
            f"license{accepted}")

    def register(self,
                 expression: str,
                 copyrights: Optional[Iterable[str]] = None,
                 provenance: str = "") -> str:
        """
        Register a part of the work.

        Args:
            expression: The SPDX license expression of the part.
            copyrights: The copyright statements of the part.
            provenance: The origin of the part, used by the error messages and
                by the traceability of an obligation.

        Returns:
            The license under which the work takes the part.

        Raises:
            ValueError: The expression is invalid, or it permits neither the
                primary license nor an accepted license.
        """
        the_license = self.select(expression, provenance)
        entry = self._entries.setdefault(the_license,
                                         LicenseEntry(the_license))
        entry.expressions.add(expression)
        if provenance:
            entry.provenance.add(provenance)
        if copyrights is not None:
            entry.copyrights.register(copyrights)
        return the_license

    def register_copyrights(self, copyrights: Iterable[str]) -> None:
        """ Register the copyright statements of the work itself. """
        entry = self._entries.setdefault(self._primary,
                                         LicenseEntry(self._primary))
        entry.copyrights.register(copyrights)

    def copyrights(self) -> Copyrights:
        """
        Are the copyrights of every part of the work.

        A produced file names every copyright holder of its parts, whatever
        the license of a part.  Only the license texts of a foreign part move
        to the package document.

        Returns:
            The copyrights of the work.
        """
        everything = Copyrights()
        for entry in self._entries.values():
            everything.register(entry.copyrights.get_statements())
        return everything

    def copyrights_of(self, the_license: Optional[str] = None) -> Copyrights:
        """
        Are the copyrights of the parts which take the license.

        Args:
            the_license: The SPDX license identifier.  None takes the primary
                license of the work.

        Returns:
            The copyrights, empty where no part takes the license.
        """
        key = self._primary if the_license is None else the_license
        entry = self._entries.get(key, None)
        return entry.copyrights if entry is not None else Copyrights()

    def __iter__(self) -> Iterator[LicenseEntry]:
        yield from sorted(self._entries.values())

    def __bool__(self) -> bool:
        return bool(self._entries)

    def foreign(self) -> list[LicenseEntry]:
        """ Are the entries of the licenses other than the primary one. """
        return [
            entry for entry in sorted(self._entries.values())
            if entry.the_license != self._primary
        ]


class LicenseProvider:
    """
    Provides the presentation of the licenses which a tree carries.

    A tree states a license as an item of the type license.  The provider
    indexes those items by their SPDX license identifier.
    """

    def __init__(self, items: Iterable[Item]) -> None:
        """
        Initialize the provider.

        Args:
            items: The items of the tree.  The provider takes the items of the
                type license.

        Raises:
            ValueError: Two items state the same identifier, or an item
                reproduces a text which it carries not.
        """
        self._items: dict[str, Item] = {}
        for item in items:
            if item.type != "license":
                continue
            identifier = item["identifier"]
            other = self._items.get(identifier, None)
            if other is not None:
                raise ValueError(f"the items {other.uid} and {item.uid} "
                                 f"state the license {identifier}")
            if item["reproduce-text"] and not item["text"]:
                raise ValueError(f"the item {item.uid} reproduces the text of "
                                 f"the license {identifier} and carries none")
            self._items[identifier] = item

    def __contains__(self, identifier: str) -> bool:
        return identifier in self._items

    def _get(self, identifier: str) -> Item:
        item = self._items.get(identifier, None)
        if item is None:
            raise ValueError(f"no item states the license {identifier}")
        return item

    def name_of(self, identifier: str) -> str:
        """
        Is the full name of the license.

        Args:
            identifier: The SPDX license identifier.

        Returns:
            The name of the license.

        Raises:
            ValueError: No item states the license.
        """
        return self._get(identifier)["name"]

    def text_of(self, identifier: str) -> Optional[str]:
        """
        Is the text which a work under the license reproduces.

        Args:
            identifier: The SPDX license identifier.

        Returns:
            The license text, or None where a work reproduces it not.

        Raises:
            ValueError: No item states the license.
        """
        item = self._get(identifier)
        return item["text"] if item["reproduce-text"] else None

    def uri_of(self, identifier: str) -> Optional[str]:
        """
        Is the uniform resource identifier of the license.

        Args:
            identifier: The SPDX license identifier.

        Returns:
            The uri, or None where the item carries none.

        Raises:
            ValueError: No item states the license.
        """
        return self._get(identifier)["uri"]
