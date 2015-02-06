# Copyright 2014 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Tests for the parsing of "['module']"s imports."""

import io
import logging
import unittest

from fades import parsing


class PyPIParsingTestCase(unittest.TestCase):
    """Check the imports parsing."""

    def test_nocomment(self):
        # note that we're testing the import at the beginning of the line, and
        # in also indented
        parsed = parsing._parse_content(io.StringIO("""import time
            import time
            from time import foo
        """))
        self.assertDictEqual(parsed, {parsing.Repo.pypi: {}})

    def test_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time
            import foo    # fades.pypi
        """))
        dep = parsed
        self.assertDictEqual(dep, {parsing.Repo.pypi: {'foo': {'version': None}}})

    def test_double(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time  # fades.pypi
            import foo    # fades.pypi
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'time': {'version': None},
                'foo': {'version': None},
            }
        })

    def test_version_same(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi == 3.5
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': '== 3.5'},
            }
        })

    def test_version_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi > 2
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': '> 2'},
            }
        })

    def test_continuation_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar
            # fades.pypi > 2
            import foo
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': '> 2'},
            }
        })

    def test_from_import_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar   # fades.pypi
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': None},
            }
        })

    def test_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo.bar   # fades.pypi
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': None},
            }
        })

    def test_from_import_complex(self):
        parsed = parsing._parse_content(io.StringIO("""
            from baz.foo import bar   # fades.pypi
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'baz': {'version': None},
            }
        })

    def test_allow_other_comments(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import *   # NOQA   # fades.pypi
        """))
        deps = parsed
        self.assertDictEqual(deps, {
            parsing.Repo.pypi: {
                'foo': {'version': None},
            }
        })

    def test_strange_import(self):
        with self.assertLogs(level=logging.WARNING) as cm:
            parsed = parsing._parse_content(io.StringIO("""
                from foo bar import :(   # fades.pypi
            """))
        self.assertEqual(cm.output[0], (
            "WARNING:fades.parsing:Not understood import info: "
            "['from', 'foo', 'bar', 'import', ':(']"
        ))
        self.assertEqual(parsed, [])

    def test_strange_fadesinfo(self):
        with self.assertLogs(level=logging.WARNING) as cm:
            parsed = parsing._parse_content(io.StringIO("""
                import foo   # fades.broken
            """))
        self.assertEqual(cm.output[0], (
            "WARNING:fades.parsing:Not understood fades info: 'fades.broken'"
        ))
        self.assertEqual(parsed, [])
