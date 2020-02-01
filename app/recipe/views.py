from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag

from .serializers import TagSerializer


class TagViewSet(
        mixins.ListModelMixin , mixins.CreateModelMixin,
        viewsets.GenericViewSet):
    """Manage tags in the database"""
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = Tag.objects.all()

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """Create a new tag"""
        serializer.save(user=self.request.user)
