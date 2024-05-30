import unittest
from unittest.mock import patch, Mock, MagicMock

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from decimal import Decimal
from app.core.models import Account, Transaction
from app.api.routes.transactions.schemas import TransactionDTO
from app.api.routes.transactions.service import (
    accept_incoming_transaction,
    create_draft_transaction,
    delete_draft,
    get_account_by_username,
    update_draft_transaction,
    get_draft_transaction_by_id,
    confirm_draft_transaction,
)


def fake_transaction_dto():
    return TransactionDTO(
        receiver_account="test_receiver",
        amount=11.30,
        category_id=1,
        description="test_description",
    )


def fake_updated_dto():
    return TransactionDTO(
        receiver_account="updated_receiver",
        amount=101.40,
        category_id=2,
        description="updated_description",
    )


def fake_transaction_draft():
    transaction = Transaction(
        sender_account=TEST_SENDER_ACCOUNT,
        receiver_account="test_receiver",
        amount=11.30,
        category_id=1,
        description="test_description",
        status="draft",
        is_flagged=False,
    )
    transaction.id = 1
    return transaction


def fake_incoming_transaction():
    transaction = Transaction(
        sender_account=TEST_SENDER_ACCOUNT,
        receiver_account="test_receiver",
        amount=11.30,
        category_id=1,
        description="test_description",
        status="pending",
        is_flagged=False,
    )
    transaction.id = 1
    return transaction


def fake_account():
    account = Account(username="test_username", balance=22, is_blocked=False)
    account.id = 1
    return account


Session = sessionmaker()


def fake_db():
    session_mock = MagicMock(spec=Session)
    session_mock.query = MagicMock()
    session_mock.query.filer = MagicMock()
    return session_mock


TEST_SENDER_ACCOUNT = "test_sender"
WRONG_SENDER_ACCOUNT = "wrong_sender"


class TransactionsServiceShould(unittest.TestCase):

    def test_createDraftTransaction_returnsTransactionWhenInputCorrect(self):
        # Arrange
        transaction = fake_transaction_dto()
        sender_account = TEST_SENDER_ACCOUNT
        db = fake_db()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()

        # Act
        result = create_draft_transaction(sender_account, transaction, db)

        expected_transaction = Transaction(
            sender_account="test_sender",
            receiver_account="test_receiver",
            amount=Decimal("11.3"),
            category_id=1,
            description="test_description",
            transaction_date=None,
            status="draft",
            is_flagged=False,
        )

        # Assert
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        self.assertIsInstance(result, Transaction)
        self.assertEqual(expected_transaction, result)

    def test_createDraftTransaction_raisesHTTPExceptionForNonExistentReceiver(self):
        # Arrange
        transaction = fake_transaction_dto()
        sender_account = TEST_SENDER_ACCOUNT
        db = fake_db()
        db.add = Mock()
        db.commit = Mock(side_effect=IntegrityError(Mock(), Mock(), "receiver_account"))
        db.rollback = Mock()

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            create_draft_transaction(sender_account, transaction, db)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Receiver doesn't exist!")

    def test_createDraftTransaction_raisesHTTPExceptionWhenCategoryIDDoesNotExist(self):
        # Arrange
        transaction = fake_transaction_dto()
        sender_account = TEST_SENDER_ACCOUNT
        db = fake_db()
        db.add = Mock()
        db.commit = Mock(side_effect=IntegrityError(Mock(), Mock(), "category_id"))
        db.rollback = Mock()

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            create_draft_transaction(sender_account, transaction, db)
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Category doesn't exist!")
        db.rollback.assert_called_once()

    @patch("app.api.routes.transactions.service.get_draft_transaction_by_id")
    def test_updateDraftTransaction_returnsUpdatedTransactionWhenInputCorrect(
        self, get_transaction_mock
    ):
        # Arrange
        transaction_id = 1
        sender_account = TEST_SENDER_ACCOUNT
        updated_transaction = fake_updated_dto()
        db = fake_db()
        db.commit = Mock()
        db.refresh = Mock()
        get_transaction_mock.return_value = fake_transaction_draft()

        # Act
        result = update_draft_transaction(
            sender_account, transaction_id, updated_transaction, db
        )

        # Assert
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        self.assertEqual(result.amount, Decimal("101.40"))
        self.assertEqual(result.receiver_account, "updated_receiver")
        self.assertEqual(result.category_id, 2)
        self.assertEqual(result.description, "updated_description")

    @patch("app.core.db_dependency.get_db")
    def test_getTransactionByID_returnsTransactionWhenExists(self, mock_get_db):
        # Arrange
        transaction_id = 1
        sender_account = "test_sender"
        db = fake_db()
        mock_get_db.return_value = db
        transaction = fake_transaction_draft()
        db.query.return_value.filter.return_value.first.return_value = transaction

        # Act
        result = get_draft_transaction_by_id(transaction_id, sender_account, db)

        # Assert
        self.assertEqual(result, transaction)
        db.query.assert_called_once_with(Transaction)
        db.query.return_value.filter.assert_called_once()
        db.query.return_value.filter.return_value.first.assert_called_once()

    @patch("app.core.db_dependency.get_db")
    def test_getTransactionByID_raises404WhenTransactionDoesNotExist(self, mock_get_db):
        # Arrange
        transaction_id = 1
        sender_account = "test_sender"
        db = fake_db()
        mock_get_db.return_value = db
        db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_draft_transaction_by_id(transaction_id, sender_account, db)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Transaction draft not found!")
        db.query.assert_called_once_with(Transaction)
        db.query.return_value.filter.assert_called_once()
        db.query.return_value.filter.return_value.first.assert_called_once()

    @patch("app.core.db_dependency.get_db")
    def test_getAccountByUsername_returnsAccountWhenExists(self, mock_get_db):
        # Arrange
        username = "test_username"
        db = fake_db()
        mock_get_db.return_value = db
        account = fake_account()
        db.query.return_value.filter.return_value.first.return_value = account

        # Act
        result = get_account_by_username(username, db)

        # Assert
        self.assertEqual(result, account)
        db.query.assert_called_once_with(Account)
        db.query.return_value.filter.assert_called_once()
        db.query.return_value.filter.return_value.first.assert_called_once()

    @patch("app.core.db_dependency.get_db")
    def test_getAccountByUsername_raises404WhenAccountIsNone(self, mock_get_db):
        # Arrange
        username = "test_username"
        db = fake_db()
        mock_get_db.return_value = db
        db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with self.assertRaises(HTTPException) as context:
            get_account_by_username(username, db)

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Account not found!")
        db.query.assert_called_once_with(Account)
        db.query.return_value.filter.assert_called_once()
        db.query.return_value.filter.return_value.first.assert_called_once()

    @patch("app.api.routes.transactions.service.get_account_by_username")
    @patch("app.api.routes.transactions.service.get_draft_transaction_by_id")
    def test_confirmDraftTransaction_returnsTransactionWithPendingStatus(
        self, get_transaction_mock, get_account_mock
    ):
        # Arrange
        sender_account = TEST_SENDER_ACCOUNT
        transaction_id = 1
        account = fake_account()
        db = fake_db()
        db.commit = Mock()
        db.refresh = Mock()
        get_transaction_mock.return_value = fake_transaction_draft()
        get_account_mock.return_value = account

        # Act
        result = confirm_draft_transaction(sender_account, transaction_id, db)

        # Assert
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        self.assertEqual(result.status, "pending")
        self.assertEqual(account.balance, 10.70)

    @patch("app.api.routes.transactions.service.get_draft_transaction_by_id")
    def test_DeleteDraft_returnsNoneWhenSuccessful(self, get_transaction_mock):
        # Arrange
        sender_account = TEST_SENDER_ACCOUNT
        transaction_id = 1
        db = fake_db()
        db.delete = Mock()
        db.commit = Mock()
        transaction = fake_transaction_draft()
        get_transaction_mock.return_value = transaction

        # Act
        result = delete_draft(sender_account, transaction_id, db)

        # Assert
        db.delete.assert_called_once_with(transaction)
        db.commit.assert_called_once()
        self.assertIsNone(result)

    @patch("app.api.routes.transactions.service.get_account_by_username")
    @patch("app.api.routes.transactions.service.get_incoming_transaction_by_id")
    def test_acceptIncomingTransaction_returnsBalanceAndChangesStatusWhenSuccessful(
        self, get_incoming_transaction_mock, get_account_mock
    ):
        # Arrange
        receiver_account = "test_receiver"
        transaction_id = 1
        account = fake_account()
        transaction = fake_incoming_transaction()
        db = fake_db()
        db.commit = Mock()
        db.refresh = Mock()
        get_account_mock.return_value = account
        get_incoming_transaction_mock.return_value = transaction

        # Act
        result = accept_incoming_transaction(receiver_account, transaction_id, db)

        # Act
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
        self.assertEqual(result, 33.30)
        self.assertEqual(transaction.status, "completed")


if __name__ == "__main__":
    unittest.main()
