from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("users:create")
TOKEN_URL = reverse("users:token")


def create_user(**params):
    user = get_user_model().objects.create(**params)
    return user.save()



class PublicUserAPITests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "email": "testemail@example.com",
            "password": "TestPassword",
            "name": "Test name"
        }
        self.token_payload = {
            "email": "testemail@example.com",
            "password": "TestPassword"
        }

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        response = self.client.post(CREATE_USER_URL, self.payload)
        user = get_user_model().objects.get(**response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_exists(self):
        """Test creating user that already exists fails"""
        self.payload = {
            "email": "testemail@example.com",
            "password": "TestPassword",
            "name": "Test name"
        }
        create_user(**self.payload)
        response = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 8 characters"""
        self.payload.update({"password": "passwor"})
        response = self.client.post(CREATE_USER_URL, self.payload)
        is_user_exists = get_user_model().objects.filter(email=self.payload["email"]).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(is_user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {
            "email": "testemail@example.com",
            "password": "TestPassword",
            "name": "Test name"
        }
        self.client.post(CREATE_USER_URL, payload)
        response = self.client.post(TOKEN_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_create_token_with_invalid_credentials(self):
        """Test that token is not created if invalid credentials are given"""
        create_user(email=self.token_payload["email"], password="passpass")
        response = self.client.post(TOKEN_URL, **self.token_payload)

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_not_valid_user(self):
        """Test that token is not created if user doesn't exist"""
        response = self.client.post(TOKEN_URL, self.token_payload)

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_missing_field(self):
        """Test that email and password are required"""
        response = self.client.post(TOKEN_URL, {"email": self.token_payload["email"], "password": ""})

        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
