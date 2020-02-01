from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from ..serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagAPITests(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagAPITests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
                'tester@example.com',
                'TestPassword'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test that authenticated user is able to retrieve tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')
        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limited_to_authenticated_user(self):
        """Test that tags returned are for the authenticated user"""
        another_user = get_user_model().objects.create_user(
                'another_tester@example.com',
                'TestPassword'
        )
        another_user_tag = Tag.objects.create(user=another_user, name='Fruity')
        main_user_tag = Tag.objects.create(user=self.user, name='Comfort Food')
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], main_user_tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        tag_payload = {'name': 'Fruity'}
        self.client.post(TAGS_URL, tag_payload)
        tags_exists = Tag.objects.filter(
                user=self.user,
                name=tag_payload['name']
        ).exists()

        self.assertTrue(tags_exists)

    def test_create_tag_with_missing_name_field(self):
        """Test that creating new tag will fail if name field is empty"""
        tag_payload = {'name': ''}
        response = self.client.post(TAGS_URL, tag_payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
