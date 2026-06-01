from django.urls import path

from . import views

app_name = "catalogs"

urlpatterns = [
    path("locations/", views.location_list, name="location-list"),
    path("locations/create/", views.location_create, name="location-create"),
    path(
        "locations/<int:location_id>/edit/",
        views.location_edit,
        name="location-edit",
    ),
    path(
        "locations/<int:location_id>/delete/",
        views.location_delete,
        name="location-delete",
    ),
]
