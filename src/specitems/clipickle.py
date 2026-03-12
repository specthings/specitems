# SPDX-License-Identifier: BSD-2-Clause
"""
Provides a command line interface to convert specification items inside
specification directories to a pickle data file.
"""

# Copyright (C) 2025 embedded brains GmbH & Co. KG
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

import argparse
import os
import pickle
import sys

from .items import ItemCache, ItemCacheConfig


def _filter(data: dict) -> dict:
    return dict((key, value) for key, value in sorted(data.items())
                if not key.startswith("_"))


def clipickle(argv: list[str] = sys.argv) -> None:
    """
    Convert specification items inside specification directories to a pickle
    data file.
    """

    parser = argparse.ArgumentParser(description=clipickle.__doc__)
    parser.add_argument("specdirs",
                        metavar="SPECIFICATION_DIRECTORIES",
                        nargs="+",
                        help="a non-empty list of specification directories")
    parser.add_argument("pickle",
                        metavar="PICKLE",
                        nargs=1,
                        help="the pickle file to generate")
    args = parser.parse_args(argv[1:])
    config = ItemCacheConfig(paths=args.specdirs, initialize_links=False)
    item_cache = ItemCache(config)
    data = dict(
        (uid, _filter(item.data)) for uid, item in sorted(item_cache.items()))
    pickle_file = args.pickle[0]
    os.makedirs(os.path.dirname(pickle_file), exist_ok=True)
    with open(pickle_file, "wb") as out:
        pickle.dump(data, out)
