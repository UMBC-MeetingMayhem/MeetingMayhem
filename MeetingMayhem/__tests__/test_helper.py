"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
import flask_unittest as test
import MeetingMayhem.helper as MMhelper
import MeetingMayhem.models as MMmodel
from flask import Flask
from flask_sqlalchemy import BaseQuery
from MeetingMayhem import app as MMapp
from MeetingMayhem import db
from random import choices
from string import ascii_letters, digits
from typing import List, Tuple, Union

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

def insert_user(role: int) -> MMmodel.User:
    r_name: str = "".join(choices(ascii_letters + digits, k=10))

    # UNIQUE constraints >:(
    user: MMmodel.User = MMmodel.User(
        username=r_name,
        email=f"{r_name}@cringe.net",
        password="gg",
        role=str(role)
    )
    db.session.add(user)
    db.session.commit()

    return user

# new class starting with create_message()
class AppSpecificHelperTests(test.ClientTestCase):
    app: Flask = MMapp
    inserted: List[Union[MMmodel.User, MMmodel.Game]] = []

    # may need these
    def setUp(self, _) -> None:
        return

    def tearDown(self, _) -> None:
        return

    def test_create_message_adversary(self, client) -> None:
        """
        create_message() is used by both adversaries and normal users.
        It returns a boolean dependant on whether or not the message was sent.
        The user sending the message, the game, the req, the form, the sender's username,
          and the timestamp of sending are all required in both cases.
        This test case is for the adversary case.
        """
        print(type(client))  # want this for strict typing (idk what client is :( )

        return

    def test_create_message_normal(self, client) -> None:
        """
        create_message() is used by both adversaries and normal users.
        It returns a boolean dependant on whether or not the message was sent.
        The user sending the message, the game, the req, the form, the sender's username,
          and the timestamp of sending are all required in both cases.
        This test case is for the normal user case.
        """

        return