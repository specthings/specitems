# SPDX-License-Identifier: BSD-2-Clause
""" Provides a formatter which uses the clang-format tool. """

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

import subprocess


class ClangFormatter:
    """Formats C language text with the clang-format tool.

    The formatter runs the clang-format tool as a subprocess.  It provides the
    mechanism to run the tool.  The policy, for example which style to use and
    what to do if the tool fails, is up to the caller.

    Attributes:
        path: The path to the clang-format executable.
        style: The style used by the clang-format tool.  The value is passed
            verbatim to the ``--style`` option of the tool.
    """

    def __init__(self, path: str, style: str) -> None:
        self.path = path
        self.style = style

    def check_available(self) -> None:
        """Check that the clang-format tool can be run.

        Raises:
            OSError: The clang-format executable could not be run.
            subprocess.CalledProcessError: The clang-format tool exited with a
                non-zero return code.
        """
        subprocess.run([self.path, "--version"],
                       capture_output=True,
                       encoding="utf-8",
                       check=True)

    def format_text(self, text: str, filename: str) -> str:
        """Format the text with the clang-format tool.

        The filename determines the language assumed by the clang-format tool
        and the directory in which the tool searches for a style file.

        Args:
            text: The text to format.
            filename: The file name assumed by the clang-format tool.

        Returns:
            The formatted text.

        Raises:
            OSError: The clang-format executable could not be run.
            subprocess.CalledProcessError: The clang-format tool exited with a
                non-zero return code.
        """
        result = subprocess.run([
            self.path, f"--style={self.style}", f"--assume-filename={filename}"
        ],
                                input=text,
                                capture_output=True,
                                encoding="utf-8",
                                check=True)
        return result.stdout
