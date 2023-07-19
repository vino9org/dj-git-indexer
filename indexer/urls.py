from django.urls import path

from . import views

app_name = "indexer"

urlpatterns = [
    path("", views.index, name=""),
    path("search", views.SearchPageView.as_view(), name="search"),
]
