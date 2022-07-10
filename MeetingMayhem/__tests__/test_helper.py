"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
import flask_unittest as test
import MeetingMayhem.helper as MMhelper
from flask import Flask
from MeetingMayhem import app as MMapp
from typing import Dict, Tuple

class HelperFxnTests(test.ClientTestCase):
    app: Flask = MMapp

    def test_check_for_str(self, _) -> None:
        """
        check_for_str() checks a string for usernames.
        It should return True if the string contains the passed username.
        Otherwise, it should return False.
        """
        CASES: Dict[Tuple[str, str], bool] = {
            ("", "Reginald"): False,  # Empty string (if str)
            ("random, longish string, with no username in, it", ">:)"): False,  # Username not in string (if (not str1[2]))
            ("Stinky, or something, lol", "lol"): True  # Username is in the string (if str1[0] == check)
        }

        for (string, check), expected in CASES.items():
            result: bool = MMhelper.check_for_str(string, check)
            self.assertEqual(result, expected)

        return

