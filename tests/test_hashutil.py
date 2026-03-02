# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the hashutil module. """

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

import os

from specitems.hashutil import (base64_to_hex, base64_to_hex_text, hash_file,
                                hash_file_md5, hash_file_sha256,
                                hash_file_lines, hash_file_lines_md5,
                                hash_file_lines_sha256)


def test_base64_to_hex():
    assert base64_to_hex("ABCD") == "001083"
    assert base64_to_hex_text("ABCD") == "0​0​1​0​8​3"


def test_hash_file(tmpdir):
    path = os.path.join(os.path.dirname(__file__), "foobar.txt")
    assert hash_file(
        path
    ) == "fNaAQG02kuQ2pdmpTmsT_e0Ujl5lGVwY0Em2XPCEAGl8vATvJZQbxzbx3r5TvKyf7MhsaSjFgQR2IVLzrMXrJg=="
    assert hash_file_sha256(
        path) == "o_6TMPuryQZm2WfSmRaVt1-WhLZkzLh85N0KcPDUa2A="
    assert hash_file_md5(path) == "IhH8liVbf3wC4nXmDh4eEQ=="
    assert hash_file_lines(
        path, []
    ) == "z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg_SpIdNs6c5H0NE8XYXysP-DGNKHfuwvY7kxvUdBeoGlODJ6-SfaPg=="
    assert hash_file_lines_sha256(
        path, []) == "47DEQpj8HBSa-_TImW-5JCeuQeRkm5NMpJWZG3hSuFU="
    assert hash_file_lines_md5(path, []) == "1B2M2Y8AsgTpgAmY7PhCfg=="
    assert hash_file_lines(
        path, [(2, 3)]
    ) == "9mawIP_zA_BOJFHgZYFP14Ff9J963kNd6BDVlVta7kdS8pgAtxV_sGMRGg8Db_ugqp9VEsxbv2QOW5lJv43VXQ=="
    assert hash_file_lines_sha256(
        path, [(2, 3)]) == "Lo1AWhfBaZdfs51JmDjsidJE2EZguoApv_UxMR--tnY="
    assert hash_file_lines_md5(path, [(2, 3)]) == "JoEuC0Tm-HxS5It4AWve9g=="
    symlink = os.path.join(tmpdir, "symlink")
    os.symlink("jumps over the lazy dog.", symlink)
    assert hash_file(
        symlink
    ) == "9mawIP_zA_BOJFHgZYFP14Ff9J963kNd6BDVlVta7kdS8pgAtxV_sGMRGg8Db_ugqp9VEsxbv2QOW5lJv43VXQ=="
