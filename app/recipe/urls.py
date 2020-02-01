from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TagViewSet, IngredientsViewSet


router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientsViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
