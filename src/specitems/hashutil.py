# SPDX-License-Identifier: BSD-2-Clause
""" Provides file hashing utility functions. """

# Copyright (C) 2020, 2026 embedded brains GmbH & Co. KG
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

import base64
import binascii
import hashlib
import os


def base64_to_hex(data: str) -> str:
    """ Convert the data in base64url encoding to the hex digits encoding. """
    binary = base64.urlsafe_b64decode(data)
    return binascii.hexlify(binary).decode("ascii")


def base64_to_hex_text(data: str) -> str:
    """
    Convert the data in base64url encoding to the hex digits encoding separated
    by invisible spaces.
    """
    binary = base64.urlsafe_b64decode(data)
    return "\u200b".join(iter(binascii.hexlify(binary).decode("ascii")))


def _hash_file(path: str, file_hash) -> str:
    if os.path.islink(path):
        file_hash.update(os.readlink(path).encode("utf-8"))
    else:
        buf = bytearray(65536)
        memview = memoryview(buf)
        with open(path, "rb", buffering=0) as src:
            for size in iter(lambda: src.readinto(memview), 0):  # type: ignore
                file_hash.update(memview[:size])
    return base64.urlsafe_b64encode(file_hash.digest()).decode("ascii")


def hash_file(path: str) -> str:
    """ Return the SHA512 digest of the file specified by path. """
    return _hash_file(path, hashlib.sha512())


def hash_file_md5(path: str) -> str:
    """ Return the MD5 digest of the file specified by path. """
    return _hash_file(path, hashlib.md5(usedforsecurity=False))


def hash_file_sha256(path: str) -> str:
    """ Return the SHA256 digest of the file specified by path. """
    return _hash_file(path, hashlib.sha256())


def _hash_file_lines(path: str, lines: list[tuple[int, int]],
                     file_hash) -> str:
    with open(path, "rb") as src:
        data = src.read().splitlines()
        for begin, end in lines:
            file_hash.update(b"\n".join(data[begin - 1:end - 1]))
    return base64.urlsafe_b64encode(file_hash.digest()).decode("ascii")


def hash_file_lines(path: str, lines: list[tuple[int, int]]) -> str:
    """
    Return the SHA512 digest of the file lines specified by the path and lines
    ranges.

    The line numbering starts with one.
    """
    return _hash_file_lines(path, lines, hashlib.sha512())


def hash_file_lines_md5(path: str, lines: list[tuple[int, int]]) -> str:
    """
    Return the MD5 digest of the file lines specified by the path and lines
    ranges.

    The line numbering starts with one.
    """
    return _hash_file_lines(path, lines, hashlib.md5(usedforsecurity=False))


def hash_file_lines_sha256(path: str, lines: list[tuple[int, int]]) -> str:
    """
    Return the SHA256 digest of the file lines specified by the path and lines
    ranges.

    The line numbering starts with one.
    """
    return _hash_file_lines(path, lines, hashlib.sha256())
