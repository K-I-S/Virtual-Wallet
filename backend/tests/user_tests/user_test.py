import unittest
from unittest.mock import patch, Mock, create_autospec

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.api.models.models import User
from app.api.routes.users.schemas import UserDTO
from app.api.routes.users.service import create
from app.api.utils.db_dependency import get_db


def fake_user_dto():
    return UserDTO(
        username="tester",
        password="password",
        email="email@example.com",
        phone_number="1234567890",
        is_admin=False,
        is_restricted=False,
    )


def fake_db():
    return create_autospec(get_db)


class UsrServices_Should(unittest.TestCase):

    @patch("app.api.routes.users.service.hash_pass")
    def test_create_returnscorrectUserWhenInoIsCorrect(self, hash_pass_mock):
        hash_pass_mock.return_value = "hashed_password"
        user = fake_user_dto()
        db = create_autospec(Session)
        # db = fake_db()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        result = create(user, db)
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        self.assertIsInstance(result, User)
        self.assertEqual(result.username, "tester")
        self.assertEqual(result.password, "hashed_password")
        self.assertEqual(result.email, "email@example.com")
        self.assertEqual(result.phone_number, "1234567890")
