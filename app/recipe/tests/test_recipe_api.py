import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient

from ..serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Return URL for recipe image upload"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredients(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required"""
        response = self.client.get(RECIPES_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
                'tester@example.com',
                'TestPassword'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
                'tester2@example.com',
                'TestPassword'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        response = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredients(user=self.user))

        url = detail_url(recipe.id)
        response = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(response.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': 5.00
        }
        response = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=response.data['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        [self.assertEqual(payload[key], getattr(recipe, key)) for key in payload.keys()]

    def test_create_recipe_with_tag(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 20.00
        }
        response = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=response.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredients1 = sample_ingredients(user=self.user, name='Prawns')
        ingredients2 = sample_ingredients(user=self.user, name='Ginger')
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredients1.id, ingredients2.id],
            'time_minutes': 20,
            'price': 7.00
        }
        response = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=response.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredients1, ingredients)
        self.assertIn(ingredients2, ingredients)

    def test_partial_update_recipe(self):
        """Test updating a recipe with patch"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {'title': 'Chicken tikka', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spaghetti',
            'time_minutes': 25,
            'price': 5.00
        }
        url = detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        [self.assertEqual(payload[key], getattr(recipe, key)) for key in payload.keys()]
        self.assertEqual(len(tags), 0)

    def test_filter_recipes_by_tags(self):
        """Test returning recipes with specific tags"""
        recipe1 = sample_recipe(user=self.user, title='Recipe1')
        recipe2 = sample_recipe(user=self.user, title='Recipe2')
        recipe3 = sample_recipe(user=self.user, title='Recipe3')
        tag1 = sample_tag(self.user, name='Tag1')
        tag2 = sample_tag(self.user, name='Tag2')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        response = self.client.get(RECIPES_URL, {'tags': f'{tag1.id},{tag2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filter_recipes_by_ingredients(self):
        """Test returning recipes with specific ingredients"""
        recipe1 = sample_recipe(user=self.user, title='Recipe1')
        recipe2 = sample_recipe(user=self.user, title='Recipe2')
        recipe3 = sample_recipe(user=self.user, title='Recipe3')
        ingredient1 = sample_ingredients(self.user, name='Ingredient1')
        ingredient2 = sample_ingredients(self.user, name='Ingredient2')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        response = self.client.get(RECIPES_URL, {'ingredients': f'{ingredient1.id},{ingredient2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)


class RecipeImageUploadTests(TestCase):
    """Test uploading images to specific recipe through the recipe API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
                'tester@example.com',
                'TestPassword'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """
        Test uploading an image to recipe
        1. Create a temporary file
        2. Write image to that file
        3. Upload that file -containing the image- through the API
        """
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            response = self.client.post(url, {'image': ntf}, format='multipart')
        self.recipe.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('image', response.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.recipe.id)
        response = self.client.post(url, {'image': 'not image'}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
