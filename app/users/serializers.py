from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializes for the users object"""

    class Meta:
        model = get_user_model()
        fields = ["email", "name", "password"]
        extra_kwargs = {
            "password": {
                "write_only": "True",
                "min_length": 8
            }
        }

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)
