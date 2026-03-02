# SPDX-License-Identifier: BSD-2-Clause
""" Test utility module. """

# Copyright (C) 2020, 2025 embedded brains GmbH & Co. KG
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
import shutil

from specitems.items import ItemCacheConfig, ItemDataByUID, load_data


def create_item_cache_config(tmp_dir: str, spec_dir: str) -> ItemCacheConfig:
    """ Creates an item cache configuration. """
    spec_src = os.path.join(os.path.dirname(__file__), spec_dir)
    spec_dst = os.path.join(tmp_dir, "spec")
    shutil.copytree(spec_src, spec_dst)
    return ItemCacheConfig(paths=[spec_dst],
                           cache_directory=os.path.join(tmp_dir, "cache"))


def get_other_type_data_by_uid() -> ItemDataByUID:
    base = os.path.dirname(__file__)
    return {
        "/spec/other":
        load_data(os.path.join(base, "spec-types/spec/other.yml")),
        "/no-type": load_data(os.path.join(base, "spec-types/no-type.yml"))
    }


def get_and_clear_log(the_caplog) -> str:
    log = "\n".join(f"{rec.levelname} {rec.message}"
                    for rec in the_caplog.records)
    the_caplog.clear()
    return log
