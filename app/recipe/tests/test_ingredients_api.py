from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from ..serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsAPITest(TestCase):
    """Test the publicly available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    """Test the private ingredients API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
                'tester@example.com',
                'TestPassword'
        )
        self.client.force_authenticate(self.user)
        self.ingredient_1 = Ingredient.objects.create(user=self.user, name='Salt')
        self.ingredient_2 = Ingredient.objects.create(user=self.user, name='Kale')

    def test_retrieve_ingredients_list(self):
        """Test retrieving a list of ingredients"""
        response = self.client.get(INGREDIENTS_URL)
        all_ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(all_ingredients, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_authenticated_user(self):
        """Test that returned ingredients for authenticated user"""
        another_user = get_user_model().objects.create_user(
                'another_tester@example.com',
                'TestPassword'
        )
        Ingredient.objects.create(user=another_user, name='Vinegar')
        response = self.client.get(INGREDIENTS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        ingredient_payload = {'name': 'Salt'}
        response = self.client.post(INGREDIENTS_URL, ingredient_payload)
        ingredient_exists = Ingredient.objects.filter(
                user=self.user,
                name=ingredient_payload['name']
        ).exists()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ingredient_exists)

    def test_create_ingredient_with_missing_name_field(self):
        """Test that creating a new ingredient will fail if name field is empty"""
        ingredient_payload = {'name': ''}
        response = self.client.post(INGREDIENTS_URL, ingredient_payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
