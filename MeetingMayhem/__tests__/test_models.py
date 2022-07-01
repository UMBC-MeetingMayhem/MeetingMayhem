"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
import flask_unittest as test
import MeetingMayhem.models as MMmodel
from MeetingMayhem import app as MMapp

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

if __name__ == "__main__":
    test.main()
