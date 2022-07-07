import flask_unittest as test
import MeetingMayhem.models as MMmodel
from flask import Flask
from MeetingMayhem import app as MMapp
from MeetingMayhem import db
from random import choices
from string import ascii_letters, digits
from typing import List

# I REALLY hate the idea of using the same DB for testing and production.
# I'm sure it'll be fine... right?? -Drew
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

# Most of these are moreso tests for sqlalchemy operations and therefore
# are probably not needed. However, they're good documentation. -Drew
class UserTests(test.ClientTestCase):
    app: Flask = MMapp
    inserted: List[MMmodel.User] = []

    def setUp(self, client) -> None:
        user1: MMmodel.User = insert_user(4)
        user2: MMmodel.User = insert_user(4)
        adversary: MMmodel.User = insert_user(3)
        gm: MMmodel.User = insert_user(2)

        self.inserted = [user1, user2, adversary, gm]
        return

    def tearDown(self, client) -> None:
        for user in self.inserted:
            db.session.delete(user)

        db.session.commit()
        self.inserted = []
        return

    def test_get_adversary(self, client) -> None:
        """
        Adversaries have role: int = 3.
        getAdversary() should return all users with this role.
        """

        return

    def test_get_all_user_adversary(self, client) -> None:
        """
        Normal users have role: int = 4, Adversaries have role: int = 3.
        getAllUserAdversary() should return all users with these roles.
        """

        return

    def test_get_non_gm_users(self, client) -> None:
        """
        Game Masters have role: int = 2 (I believe).
        getNonGMUsers() should return all users with role: int > 2.
        """

        return

# Putting nothing in this class for now-- no functional operations
# are performed on this model. May be worth looking into decorating it
# with dataclasses.dataclass. -Drew
# https://python.plainenglish.io/why-you-should-start-using-pythons-dataclasses-cd6a73ae5614
class MessageTests(test.ClientTestCase):
    app = MMapp

    def setUp(self, client) -> None:
        return

    def tearDown(self, client) -> None:
        return

# See the UserTests comment. -Drew
class GameTests(test.ClientTestCase):
    app = MMapp

    def setUp(self, client) -> None:
        return

    def tearDown(self, client) -> None:
        return

    def test_get_game(self, client) -> None:
        """
        Games have an is_running field.
        getGame() should only return games that are currently in progress.
        """

        return


if __name__ == "__main__":
    test.main()
