from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("users:create")


def create_user(**params):
    return get_user_model().objects.create(**params)


class PublicUserAPITests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "email": "testemail@example.com",
            "password": "TestPassword",
            "name": "Test name"
        }
        response = self.client.post(CREATE_USER_URL, payload)
        user = get_user_model().objects.get(**response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_exists(self):
        """Test creating user that already exists fails"""
        payload = {
            "email": "testemail@example.com",
            "password": "TestPassword",
            "name": "Test name"
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password must be more than 8 characters"""
        payload = {
            "email": "testemail@example.com",
            "password": "passwor",
            "name": "Test name"
        }
        response = self.client.post(CREATE_USER_URL, payload)
        is_user_exists = get_user_model().objects.filter(email=payload["email"]).exists()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(is_user_exists)
