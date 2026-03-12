# SPDX-License-Identifier: BSD-2-Clause
""" Provides a command line interface to hash a list of files. """

# Copyright (C) 2023, 2026 embedded brains GmbH & Co. KG
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
import sys

from .hashutil import (base64_to_hex, hash_file, hash_file_lines,
                       hash_file_md5, hash_file_lines_md5, hash_file_sha256,
                       hash_file_lines_sha256)

_HASH_FILE = {
    "MD5": hash_file_md5,
    "SHA256": hash_file_sha256,
    "SHA512": hash_file
}

_HASH_FILE_LINES = {
    "MD5": hash_file_lines_md5,
    "SHA256": hash_file_lines_sha256,
    "SHA512": hash_file_lines
}


def _identity(digest: str) -> str:
    return digest


_FORMATTER = {"base64url": _identity, "hex": base64_to_hex}


def clihash(argv: list[str] = sys.argv) -> None:
    """ Hash the list of files. """
    parser = argparse.ArgumentParser(description=clihash.__doc__)
    parser.add_argument('--algorithm',
                        choices=["MD5", "SHA256", "SHA512"],
                        type=str.upper,
                        default="SHA512",
                        help="hash algorithm (default: SHA512)")
    parser.add_argument('--format',
                        choices=["base64url", "hex"],
                        type=str.lower,
                        default="base64url",
                        help="digest format (default: base64url)")
    parser.add_argument('--line',
                        action="append",
                        default=None,
                        help=("hash line B (format: B) or lines "
                              "from B to E excluding E (format B:E); "
                              "the line numbering starts with one"))
    parser.add_argument("files",
                        metavar="FILES",
                        nargs="+",
                        help="the files to hash")
    args = parser.parse_args(argv[1:])
    formatter = _FORMATTER[args.format]
    if args.line:
        lines: list[tuple[int, int]] = []
        do_hash_file_lines = _HASH_FILE_LINES[args.algorithm]
        for line in args.line:
            begin, _, end = line.partition(":")
            if not end:
                end = int(begin) + 1
            lines.append((int(begin), int(end)))
        for path in args.files:
            print(path, formatter(do_hash_file_lines(path, lines)))
    else:
        do_hash_file = _HASH_FILE[args.algorithm]
        for path in args.files:
            print(path, formatter(do_hash_file(path)))
