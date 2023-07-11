from django.urls import path

from . import views

app_name = "Git Indexer"

urlpatterns = [
    path("", views.SearchPageView.as_view(), name="search"),
]
