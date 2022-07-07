"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
import flask_unittest as test
import MeetingMayhem.models as MMmodel
from MeetingMayhem import app as MMapp

"""
class Ex(test.ClientTestCase):
    app = MMapp  # app obj goes here when ready

    def setUp(self, client) -> None:
        return

    def tearDown(self, client) -> None:
        return

    def test_basic_assertion(self, client) -> None:
        self.assertEqual(1, 1)
        self.assertTrue(1 == 1)
        self.assertFalse(1 == 2)

        return
"""

# Most of these are moreso tests for sqlalchemy operations and therefore
# are probably not needed. However, they're good documentation. -Drew
class UserTests(test.ClientTestCase):
    app = MMapp  # app obj goes here when ready

    def setUp(self, client) -> None:
        return

    def tearDown(self, client) -> None:
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
