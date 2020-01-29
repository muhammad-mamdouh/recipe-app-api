from django.urls import path, include

from .views import CreateUserView


app_name = "users"
urlpatterns = [
    path('create/', CreateUserView.as_view(), name="create"),
]
