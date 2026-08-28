"""URL routing для contacts приложения."""

from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.contacts_index, name="index"),
]
