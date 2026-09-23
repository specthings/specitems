# SPDX-License-Identifier: BSD-2-Clause
""" Provides interfaces for content generation. """

# Copyright (C) 2019, 2026 embedded brains GmbH & Co. KG
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

import re
from typing import Iterable, Optional, Union


def split_copyright_statement(statement: str) -> tuple[str, set[int]]:
    """ Split the copyright statement into the holder and year set. """
    match = re.search(
        r"^\s*Copyright\s+\(C\)\s+([0-9]+),\s*([0-9]+)\s+(.+)\s*$",
        statement,
        flags=re.I,
    )
    if match:
        return match.group(3), set((int(match.group(1)), int(match.group(2))))
    match = re.search(
        r"^\s*Copyright\s+\(C\)\s+([0-9]+)\s*-\s*([0-9]+)\s+(.+)\s*$",
        statement,
        flags=re.I,
    )
    if match:
        return match.group(3), set((int(match.group(1)), int(match.group(2))))
    match = re.search(
        r"^\s*Copyright\s+\(C\)\s+([0-9]+)\s+(.+)\s*$",
        statement,
        flags=re.I,
    )
    if match:
        return match.group(2), set((int(match.group(1)), ))
    raise ValueError(statement)


def make_copyright_statement(holder: str,
                             years: set[int],
                             line: str = "Copyright (C)") -> str:
    """ Make the copyright statement from the holder and year set. """
    year_count = len(years)
    line += f" {min(years)}"
    if year_count > 1:
        line += f", {max(years)}"
    line += f" {holder}"
    return line


class Copyright:
    """
    Represents a copyright holder with its years of substantial contributions.
    """

    @classmethod
    def from_statement(cls, statement: str) -> "Copyright":
        """ Make a copyright from the statement. """
        holder, years = split_copyright_statement(statement)
        return Copyright(holder, years)

    def __init__(self, holder: str, years: Optional[set[int]] = None):
        self.holder = holder
        self.years = years if years is not None else set()

    def add_year(self, year: int):
        """
        Add the year to the set of substantial contributions of this copyright
        holder.
        """
        self.years.add(year)

    def get_statement(self, line: str = "Copyright (C)") -> str:
        """ Return the associated copyright statement. """
        return make_copyright_statement(self.holder, self.years, line)

    def __lt__(self, other: "Copyright") -> bool:
        return (min(self.years), max(self.years),
                other.holder) < (min(other.years), max(other.years),
                                 self.holder)


def _copyright_key(holder_years):
    return (-min(holder_years[1]), -max(holder_years[1]), holder_years[0])


class Copyrights(dict):
    """ Represents a set of copyright holders. """

    def register(self, statements: Union[str, Iterable[str]]) -> None:
        """ Register the copyright statement. """
        if isinstance(statements, str):
            statements = [statements]
        for statement in statements:
            holder, years = split_copyright_statement(statement)
            self.setdefault(holder, set()).update(years)

    def get_statements(self, line: str = "Copyright (C)") -> list[str]:
        """ Return all registered copyright statements as a sorted list. """
        return [
            make_copyright_statement(holder, years, line)
            for holder, years in sorted(self.items(), key=_copyright_key)
        ]
