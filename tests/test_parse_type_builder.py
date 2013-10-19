#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test suite  for parse_type.py

REQUIRES: parse >= 1.5.3.1 ('pattern' attribute support)
"""

from .parse_type_test import ParseTypeTestCase
from .parse_type_test import parse_yesno, parse_person_choice
from parse_type import TypeBuilder, build_type_dict
from enum import Enum
import parse
import unittest


# -----------------------------------------------------------------------------
# TEST CASE: TestTypeBuilder4Enum
# -----------------------------------------------------------------------------
class TestTypeBuilder4Enum(ParseTypeTestCase):

    TYPE_CONVERTERS = [ parse_yesno ]

    def ensure_can_parse_all_enum_values(self, parser, type_converter, schema, name):
        # -- ENSURE: Known enum values are correctly extracted.
        for value_name, value in type_converter.mappings.items():
            text = schema % value_name
            self.assert_match(parser, text, name,  value)

    def test_parse_enum_yesno(self):
        extra_types = build_type_dict([ parse_yesno ])
        schema = "Answer: {answer:YesNo}"
        parser = parse.Parser(schema, extra_types)

        # -- PERFORM TESTS:
        self.ensure_can_parse_all_enum_values(parser,
                parse_yesno, "Answer: %s", "answer")

        # -- VALID:
        self.assert_match(parser, "Answer: yes", "answer", True)
        self.assert_match(parser, "Answer: no",  "answer", False)

        # -- IGNORE-CASE: In parsing, calls type converter function !!!
        self.assert_match(parser, "Answer: YES", "answer", True)

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __YES__", "answer")
        self.assert_mismatch(parser, "Answer: yes ",    "answer")
        self.assert_mismatch(parser, "Answer: yes ZZZ", "answer")

    def test_make_enum_with_dict(self):
        parse_nword = TypeBuilder.make_enum({"one": 1, "two": 2, "three": 3})
        parse_nword.name = "NumberAsWord"

        extra_types = build_type_dict([ parse_nword ])
        schema = "Answer: {number:NumberAsWord}"
        parser = parse.Parser(schema, extra_types)

        # -- PERFORM TESTS:
        self.ensure_can_parse_all_enum_values(parser,
            parse_nword, "Answer: %s", "number")

        # -- VALID:
        self.assert_match(parser, "Answer: one", "number", 1)
        self.assert_match(parser, "Answer: two", "number", 2)

        # -- IGNORE-CASE: In parsing, calls type converter function !!!
        self.assert_match(parser, "Answer: THREE", "number", 3)

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __one__", "number")
        self.assert_mismatch(parser, "Answer: one ",    "number")
        self.assert_mismatch(parser, "Answer: one_",    "number")
        self.assert_mismatch(parser, "Answer: one ZZZ", "number")

    def test_make_enum_with_enum_class(self):
        """
        Use :meth:`parse_type.TypeBuilder.make_enum()` with enum34 classes.
        """
        class Color(Enum):
            red = 1
            green = 2
            blue = 3

        parse_color = TypeBuilder.make_enum(Color)
        parse_color.name = "Color"
        schema = "Answer: {color:Color}"
        parser = parse.Parser(schema, dict(Color=parse_color))

        # -- PERFORM TESTS:
        self.ensure_can_parse_all_enum_values(parser,
                parse_color, "Answer: %s", "color")

        # -- VALID:
        self.assert_match(parser, "Answer: red",   "color", Color.red)
        self.assert_match(parser, "Answer: green", "color", Color.green)
        self.assert_match(parser, "Answer: blue",  "color", Color.blue)

        # -- IGNORE-CASE: In parsing, calls type converter function !!!
        self.assert_match(parser, "Answer: RED", "color", Color.red)

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __RED__", "color")
        self.assert_mismatch(parser, "Answer: red ",    "color")
        self.assert_mismatch(parser, "Answer: redx",    "color")
        self.assert_mismatch(parser, "Answer: redx ZZZ", "color")


# -----------------------------------------------------------------------------
# TEST CASE: TestTypeBuilder4Choice
# -----------------------------------------------------------------------------
class TestTypeBuilder4Choice(ParseTypeTestCase):

    def ensure_can_parse_all_choices(self, parser, type_converter, schema, name):
        for choice_value in type_converter.choices:
            text = schema % choice_value
            self.assert_match(parser, text, name,  choice_value)

    def ensure_can_parse_all_choices2(self, parser, type_converter, schema, name):
        for index, choice_value in enumerate(type_converter.choices):
            text = schema % choice_value
            self.assert_match(parser, text, name, (index, choice_value))

    def test_parse_choice_persons(self):
        extra_types = build_type_dict([ parse_person_choice ])
        schema = "Answer: {answer:PersonChoice}"
        parser = parse.Parser(schema, extra_types)

        # -- PERFORM TESTS:
        self.assert_match(parser, "Answer: Alice", "answer", "Alice")
        self.assert_match(parser, "Answer: Bob",   "answer", "Bob")
        self.ensure_can_parse_all_choices(parser,
                    parse_person_choice, "Answer: %s", "answer")

        # -- IGNORE-CASE: In parsing, calls type converter function !!!
        # SKIP-WART: self.assert_match(parser, "Answer: BOB", "answer", "BOB")

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __Alice__", "answer")
        self.assert_mismatch(parser, "Answer: Alice ",    "answer")
        self.assert_mismatch(parser, "Answer: Alice ZZZ", "answer")

    def test_make_choice(self):
        parse_choice = TypeBuilder.make_choice(["one", "two", "three"])
        parse_choice.name = "NumberWordChoice"
        extra_types = build_type_dict([ parse_choice ])
        schema = "Answer: {answer:NumberWordChoice}"
        parser = parse.Parser(schema, extra_types)

        # -- PERFORM TESTS:
        self.assert_match(parser, "Answer: one", "answer", "one")
        self.assert_match(parser, "Answer: two", "answer", "two")
        self.ensure_can_parse_all_choices(parser,
                    parse_choice, "Answer: %s", "answer")

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __one__", "answer")
        self.assert_mismatch(parser, "Answer: one ",    "answer")
        self.assert_mismatch(parser, "Answer: one ZZZ", "answer")

    def test_make_choice2(self):
        parse_choice2 = TypeBuilder.make_choice2(["zero", "one", "two"])
        parse_choice2.name = "NumberWordChoice2"
        extra_types = build_type_dict([ parse_choice2 ])
        schema = "Answer: {answer:NumberWordChoice2}"
        parser = parse.Parser(schema, extra_types)

        # -- PERFORM TESTS:
        self.assert_match(parser, "Answer: zero", "answer", (0, "zero"))
        self.assert_match(parser, "Answer: one",  "answer", (1, "one"))
        self.assert_match(parser, "Answer: two",  "answer", (2, "two"))
        self.ensure_can_parse_all_choices2(parser,
                parse_choice2, "Answer: %s", "answer")

        # -- PARSE MISMATCH:
        self.assert_mismatch(parser, "Answer: __one__", "answer")
        self.assert_mismatch(parser, "Answer: one ",    "answer")
        self.assert_mismatch(parser, "Answer: one ZZZ", "answer")

# -----------------------------------------------------------------------------
# MAIN:
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    unittest.main()


# Copyright (c) 2012-2013 by Jens Engel (https://github/jenisys/parse_type)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
