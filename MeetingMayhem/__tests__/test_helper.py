"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
import flask_unittest as test
import MeetingMayhem.helper as MMhelper
from flask import Flask
from MeetingMayhem import app as MMapp
from typing import Dict, List, Tuple

class HelperFxnTests(test.ClientTestCase):
    app: Flask = MMapp

    def test_check_for_str(self, _) -> None:
        """
        check_for_str() checks a string for usernames.
        It should return True if the string contains the passed username.
        Otherwise, it should return False.
        """
        CASES: List[Tuple[Tuple[str, str], bool]] = {
            (("", "Reginald"), False),
            (("random, longish string, with no username in, it", ">:)"), False),
            (("Stinky, or something, lol", "lol"), True)
        }

        for (string, check), expected in CASES:
            result: bool = MMhelper.check_for_str(string, check)
            self.assertEqual(result, expected)

        return

    def test_strip_list_str(self, _) -> None:
        """
        strip_list_str() filters a list of strings from commas and trailing whitespace.
        Lists containing strings with commas/trailing whitespace will be returned as filtered.
        Lists containing strings that do not need filtering are returned as-is.
        Empty lists are returned as-is.
        """
        CASES: List[Tuple[List[str], List[str]]] = [
            (["bringus,  ", "dinkus,,,    ", "stinkus, l;asdjf"], ["bringus", "dinkus", "stinkus"]),
            (["aa", "bb", "cc"], ["aa", "bb", "cc"]),
            ([], []),
            ([", "], [""])
        ]

        for inp, expected_out in CASES:
            result: List[str] = MMhelper.strip_list_str(inp)
            self.assertEqual(result, expected_out)

        return

    def test_str_to_list(self, _) -> None:
        """
        str_to_list() acts similarly to str.split(', '), but takes a list as an arg.
        A TypeError should be raised if positional args are not str, list respectively.
        Similarly, a TypeError should be raised if an empty string is passed.
        Worth noting: documentation states an empty list must be passed-- no validation is in place for this.
        """
        CASES: List[Tuple[str, List[str]]] = [
            ("string, delimited, by, commas", "string, delimited, by, commas".split(', ')),
            ("long     , comma", ["long     ", "comma"]),
            ("gg, ", ["gg"])
        ]

        for inp, expected_out in CASES:
            result: List[str] = MMhelper.str_to_list(inp, [])
            self.assertEqual(result, expected_out)

        with self.assertRaises(TypeError): MMhelper.str_to_list(1, 2)
        with self.assertRaises(TypeError): MMhelper.str_to_list("", [])

        return

# new class starting with create_message()
