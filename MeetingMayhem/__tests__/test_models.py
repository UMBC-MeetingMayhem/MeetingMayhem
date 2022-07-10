from re import L
import flask_unittest as test
import MeetingMayhem.models as MMmodel
from flask import Flask
from flask_sqlalchemy import BaseQuery
from MeetingMayhem import app as MMapp
from MeetingMayhem import db
from random import choices
from string import ascii_letters, digits
from typing import List, Tuple

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
    base_num_users: int = MMmodel.User.query.filter_by(role=4).count()
    base_num_adv: int = MMmodel.User.query.filter_by(role=3).count()
    base_num_gm: int = MMmodel.User.query.filter_by(role=2).count()

    def setUp(self, _) -> None:
        user1: MMmodel.User = insert_user(4)
        user2: MMmodel.User = insert_user(4)
        adversary: MMmodel.User = insert_user(3)
        gm: MMmodel.User = insert_user(2)

        self.inserted = [user1, user2, adversary, gm]
        return

    def tearDown(self, _) -> None:
        for user in self.inserted:
            db.session.delete(user)

        db.session.commit()
        self.inserted = []
        return

    def test_get_adversary(self, _) -> None:
        """
        Adversaries have role: int = 3.
        getAdversary() should return all users with this role.
        """
        result: List[MMmodel.User] = list(MMmodel.getAdversary())
        diff: int = len(result) - self.base_num_adv
        self.assertEqual(diff, 1)
        self.assertTrue(self.inserted[2] in result)

        return

    def test_get_all_user_adversary(self, _) -> None:
        """
        Normal users have role: int = 4, Adversaries have role: int = 3.
        getAllUserAdversary() should return all users with these roles.
        """
        result: BaseQuery = MMmodel.getAllUserAdversary()
        diff: int = result.count() - (self.base_num_users + self.base_num_adv)
        self.assertEqual(diff, 3)
        self.assertTrue(all([self.inserted[i] in result for i in range(3)]))

        return

    def test_get_non_gm_users(self, _) -> None:
        """
        Game Masters have role: int = 2 (I believe).
        getNonGMUsers() should return all users with role: int > 2.
        """
        result: BaseQuery = MMmodel.getNonGMUsers()
        diff: int = result.count() - (self.base_num_users + self.base_num_adv)
        self.assertEqual(diff, 3)
        self.assertTrue(all([self.inserted[i] in result for i in range(3)]))

        return

# Putting nothing in this class for now-- no functional operations
# are performed on this model. May be worth looking into decorating it
# with dataclasses.dataclass. -Drew
# https://python.plainenglish.io/why-you-should-start-using-pythons-dataclasses-cd6a73ae5614
class MessageTests(test.ClientTestCase):
    app: Flask = MMapp

    def setUp(self, _) -> None:
        return

    def tearDown(self, _) -> None:
        return

# See insert_user() for me complaining. -Drew
def create_game(*, running: bool) -> Tuple[MMmodel.Game, MMmodel.User]:
    adv: MMmodel.User = insert_user(3)
    game: MMmodel.Game = MMmodel.Game(
        name=f"{'' if running else 'Not '}Running Game",
        is_running=running,
        adversary=adv.username,
        players="",
        current_round=1,
        adv_current_msg=1,
        adv_current_msg_list_size=1
    )
    db.session.add(game)
    db.session.commit()

    return game, adv

# See the UserTests comment. -Drew
class GameTests(test.ClientTestCase):
    app: Flask = MMapp
    inserted: List[MMmodel.Game] = []
    base_num_running: int = MMmodel.Game.query.filter_by(is_running=True).count()

    def setUp(self, _) -> None:
        running_details: Tuple[MMmodel.Game, MMmodel.User] = create_game(running=True)
        not_running_details: Tuple[MMmodel.Game, MMmodel.User] = create_game(running=False)

        self.inserted = [*running_details, *not_running_details]
        return

    def tearDown(self, _) -> None:
        for item in self.inserted:
            db.session.delete(item)

        db.session.commit()
        self.inserted = []
        return

    def test_get_game(self, _) -> None:
        """
        Games have an is_running field.
        getGame() should only return games that are currently in progress.
        """
        result: List[MMmodel.Game] = list(MMmodel.getGame())
        diff: int = len(result) - self.base_num_running
        self.assertEqual(diff, 1)
        self.assertTrue(self.inserted[0] in result)
        self.assertTrue(self.inserted[2] not in result)

        return


if __name__ == "__main__":
    test.main()
