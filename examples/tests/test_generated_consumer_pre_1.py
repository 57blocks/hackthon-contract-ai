import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from requests.exceptions import HTTPError
from consumer_module import User, UserConsumer  # Assuming the code is in consumer_module.py

class TestUser(unittest.TestCase):

    def test_valid_user(self):
        user = User(id=1, name="John Doe", created_on=datetime.now())
        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, "John Doe")

    def test_user_empty_name(self):
        with self.assertRaises(ValueError) as context:
            User(id=1, name="", created_on=datetime.now())
        self.assertEqual(str(context.exception), "User must have a name")

    def test_user_negative_id(self):
        with self.assertRaises(ValueError) as context:
            User(id=-1, name="John Doe", created_on=datetime.now())
        self.assertEqual(str(context.exception), "User ID must be a positive integer")


class TestUserConsumer(unittest.TestCase):

    def setUp(self):
        self.consumer = UserConsumer(base_uri="http://localhost")

    @patch('requests.get')
    def test_get_user_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "name": "John Doe",
            "created_on": "2023-01-01T00:00:00"
        }
        mock_get.return_value = mock_response

        user = self.consumer.get_user(1)
        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, "John Doe")

    @patch('requests.get')
    def test_get_user_http_error(self, mock_get):
        mock_get.side_effect = HTTPError("Error fetching user")

        with self.assertRaises(HTTPError):
            self.consumer.get_user(1)

    @patch('requests.post')
    def test_create_user_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 1,
            "name": "John Doe",
            "created_on": "2023-01-01T00:00:00"
        }
        mock_post.return_value = mock_response

        user = self.consumer.create_user(name="John Doe")
        self.assertEqual(user.id, 1)
        self.assertEqual(user.name, "John Doe")

    @patch('requests.post')
    def test_create_user_http_error(self, mock_post):
        mock_post.side_effect = HTTPError("Error creating user")

        with self.assertRaises(HTTPError):
            self.consumer.create_user(name="John Doe")

    @patch('requests.delete')
    def test_delete_user_success(self, mock_delete):
        mock_response = MagicMock()
        mock_delete.return_value = mock_response

        try:
            self.consumer.delete_user(1)
        except HTTPError as e:
            self.fail(f"delete_user raised HTTPError unexpectedly: {str(e)}")

    @patch('requests.delete')
    def test_delete_user_http_error(self, mock_delete):
        mock_delete.side_effect = HTTPError("Error deleting user")

        with self.assertRaises(HTTPError):
            self.consumer.delete_user(1)

if __name__ == '__main__':
    unittest.main()