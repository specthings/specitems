# SPDX-License-Identifier: BSD-2-Clause
""" Provides support for person and organization items. """

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

import dataclasses
from typing import Iterable, Optional

from .items import Item, Link


def is_valid_affiliation(link: Link, date: Optional[str]) -> bool:
    """
    Return true, if the affiliation link is valid at the date.

    The date is either an ISO 8601 date or a year.  The comparison uses the
    precision of the date.  Without a date, the affiliations without an end
    are valid.
    """
    begin = link.data.get("from", None)
    end = link.data.get("until", None)
    if date is None:
        return end is None
    return ((begin is None or begin[:len(date)] <= date)
            and (end is None or date <= end[:len(date)]))


def get_affiliations(persons: Iterable[Item],
                     date: Optional[str]) -> list[Item]:
    """
    Get the organizations of the persons which are valid at the date.

    The organizations are unique and ordered by the persons and their links.
    """
    organizations: dict[Item, None] = {}
    for person in persons:
        for link in person.links_to_parents("affiliation"):
            if is_valid_affiliation(link, date):
                organizations[link.item] = None
    return list(organizations)


@dataclasses.dataclass(frozen=True)
class Person:
    """ Represents the person of a person item. """

    #: The person item.
    item: Item

    @property
    def name(self) -> str:
        """ The name of the person, a role, or a pseudonym. """
        return self.item["name"]

    @property
    def first_name(self) -> Optional[str]:
        """ The first names of the person, if the person has first names. """
        return self.item.get("first-name", None)

    @property
    def full_name(self) -> str:
        """ The name which documents show, the first names and the name. """
        first_name = self.first_name
        return self.name if first_name is None else f"{first_name} {self.name}"

    def affiliations(self, date: Optional[str]) -> list[Item]:
        """
        Get the organizations of the person which are valid at the date.

        The organizations are ordered by the affiliation links.
        """
        return get_affiliations([self.item], date)
