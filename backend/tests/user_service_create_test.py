import unittest
from unittest.mock import patch, Mock, create_autospec

from sqlalchemy.exc import IntegrityError
#from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.api.models.models import User
from backend.app.api.routes.users.schemas import UserDTO
from backend.app.api.routes.users.service import create
from backend.app.api.utils.db_dependency import get_db


def fake_user_dto():
    return UserDTO(
        username="tester",
        password="password",
        email="email@example.com",
        phone_number="1234567890",
        is_admin=False,
        is_restricted=False
    )
def fake_db():
    return create_autospec(get_db)

class UsrServices_Should(unittest.TestCase):

    @patch('app.api.routes.users.service.hash_pass')
    def test_create_returnscorrectUserWhenInoIsCorrect(self, hash_pass_mock):
        hash_pass_mock.return_value = "hashed_password"
        user = fake_user_dto()
        db = fake_db()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        result = create(user, db)
        db.add.assert_called_once( )
        db.commit.assert_called_once( )
        db.refresh.assert_called_once( )
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, "tester")
        self.assertEqual(result.password, "hashed_password")
        self.assertEqual(result.email, "email@example.com")
        self.assertEqual(result.phone_number, "1234567890")


    @patch('app.api.routes.users.service.hash_pass')
    def test_create_returnsCorrectErrorWhenUsernameExists(self, hash_pass_mock):

        hash_pass_mock.return_value = "hashed_password"
        user_dto = fake_user_dto()
        db = fake_db()
        db.add = Mock()
        db.commit = Mock(side_effect=IntegrityError(Mock(), Mock(), "Duplicate entry 'tester' for key 'username'"))
        db.rollback = Mock()

        with self.assertRaises(HTTPException) as context:
            create(user_dto, db)

        db.rollback.assert_called_once( )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Username already exists")

    @patch('app.api.routes.users.service.hash_pass')
    def test_create_returnsCorrectErrorWhenPhoneNumberExists(self, hash_pass_mock):
        hash_pass_mock.return_value = "hashed_password"
        user_dto = fake_user_dto( )
        db = fake_db()
        db.add = Mock( )
        db.commit = Mock(
            side_effect=IntegrityError(Mock(), Mock(), "Duplicate entry '1234567890' for key 'phone_number'"))
        db.rollback = Mock()

        with self.assertRaises(HTTPException) as context:
            create(user_dto, db)
        db.rollback.assert_called_once( )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Phone number already exists")

    @patch('app.api.routes.users.service.hash_pass')
    def test_create_returnsCorrectErrorWhenEmailExists(self, hash_pass_mock):
        hash_pass_mock.return_value = "hashed_password"
        user_dto = fake_user_dto( )
        db = fake_db()
        db.add = Mock( )
        db.commit = Mock(
            side_effect=IntegrityError(Mock( ), Mock( ), "Duplicate entry 'email@example.com' for key 'email'"))
        db.rollback = Mock( )

        with self.assertRaises(HTTPException) as context:
            create(user_dto, db)

        db.rollback.assert_called_once( )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Email already exists")

    @patch('app.api.routes.users.service.hash_pass')
    def test_create_returnsCorrectErrorWhenInvalidDataIsPutSomehow(self, hash_pass_mock):
        hash_pass_mock.return_value = "hashed_password"
        user_dto = fake_user_dto( )
        db = fake_db()
        db.add = Mock( )
        db.commit = Mock(side_effect=IntegrityError(Mock( ), Mock( ), "Some other integrity error"))
        db.rollback = Mock( )

        with self.assertRaises(HTTPException) as context:
            create(user_dto, db)

        db.rollback.assert_called_once( )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Could not complete registration")

