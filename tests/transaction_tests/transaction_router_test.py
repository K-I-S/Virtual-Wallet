import asyncio
import unittest
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, Mock, MagicMock, create_autospec
from fastapi.testclient import TestClient
from app.main import app
from app.api.auth_service.auth import authenticate_user
from app.api.routes.users.schemas import UserDTO, UpdateUserDTO, UserViewDTO
from app.core.models import Transaction
from app.api.routes.transactions.schemas import TransactionDTO
from app.api.routes.transactions.router import create_draft_transaction


client = TestClient(app)


def fake_transaction():
    mock_transaction = MagicMock(spec=Transaction)
    mock_transaction.id = 2
    mock_transaction.sender_account = "test_sender"
    mock_transaction.receiver_account = "test_receiver"
    mock_transaction.amount = 11.20
    mock_transaction.category_id = 1
    mock_transaction.description = "test_description"
    mock_transaction.transaction_date = None
    mock_transaction.status = "draft"
    mock_transaction.is_reccurring = False
    mock_transaction.recurring_interval = None
    mock_transaction.is_flagged = False
    return mock_transaction


def fake_transaction_dto():
    return TransactionDTO(
        receiver_account="test_receiver",
        amount=11.30,
        category_id=1,
        description="test_description",
    )


Session = sessionmaker()


def fake_db():
    return MagicMock()


def fake_user_view():
    return UserViewDTO(id=1, username="testuser")


class TransactionRouter_Should(unittest.TestCase):

    @patch("app.core.db_dependency.get_db")
    @patch("app.api.routes.transactions.service.create_draft_transaction")
    @patch("app.api.auth_service.auth.get_user_or_raise_401")
    def test_createDraftTransaction_IsSuccessful(
        self, mock_get_db, create_draft_transaction_mock, get_user_mock
    ):
        # Arrange
        get_user_mock.return_value = fake_user_view()
        transaction_dto = fake_transaction_dto()
        mock_get_db.return_value = fake_db()
        db = fake_db()
        create_draft_transaction_mock.return_value = fake_transaction()
        user = fake_user_view()

        # Act
        response = create_draft_transaction(user, transaction_dto, db)

        # Assert
        self.assertEqual(
            response, "You are about to send 11.20 to test_receiver [Draft ID: 2]"
        )