# SPDX-License-Identifier: BSD-2-Clause
""" Provides functions to run a subprocess action. """

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

import copy
import logging
import os
import subprocess


def _env_clear(uid: str, env: dict, _action: dict[str, str]) -> None:
    logging.info("%s: env: clear", uid)
    env.clear()


def _env_ignore(uid: str, _env: dict, _action: dict[str, str]) -> None:
    logging.info("%s: env: ignore action", uid)


def _env_path_append(uid: str, env: dict, action: dict[str, str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: append '%s' to %s", uid, value, name)
    env[name] = f"{env[name]}:{value}"


def _env_path_prepend(uid: str, env: dict, action: dict[str, str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: prepend '%s' to %s", uid, value, name)
    env[name] = f"{value}:{env[name]}"


def _env_set(uid: str, env: dict, action: dict[str, str]) -> None:
    name = action["name"]
    value = action["value"]
    logging.info("%s: env: %s = '%s'", uid, name, value)
    env[name] = value


def _env_unset(uid: str, env: dict, action: dict[str, str]) -> None:
    name = action["name"]
    logging.info("%s: env: unset %s", uid, name)
    del env[name]


_ENV_ACTIONS = {
    "clear": _env_clear,
    "ignore": _env_ignore,
    "path-append": _env_path_append,
    "path-prepend": _env_path_prepend,
    "set": _env_set,
    "unset": _env_unset
}


def make_subprocess_environment(uid: str,
                                env_actions: list[dict]) -> dict | None:
    """ Make a subprocess environment using the environment actions. """
    env: dict | None = None
    if env_actions:
        logging.info("%s: env: modify", uid)
        env = copy.deepcopy(os.environ.copy())
        for env_action in env_actions:
            _ENV_ACTIONS[env_action["action"]](uid, env, env_action)
    return env


def run_subprocess_action(uid: str, action: dict) -> None:
    """ Run the command specified by the action as a subprocess. """
    env = make_subprocess_environment(uid, action["env"])
    cmd = action["command"]
    cwd = action["working-directory"]
    logging.info("%s: run in '%s': %s", uid, cwd,
                 " ".join(f"'{i}'" for i in cmd))
    stdout = action.get("stdout", None)
    if stdout is None:
        status = subprocess.run(cmd, env=env, check=False, cwd=cwd)
    else:
        with open(stdout, "wb") as stdout_file:
            status = subprocess.run(cmd,
                                    env=env,
                                    check=False,
                                    cwd=cwd,
                                    stdout=stdout_file)
    expected_return_code = action["expected-return-code"]
    if expected_return_code is not None:
        assert status.returncode == expected_return_code
