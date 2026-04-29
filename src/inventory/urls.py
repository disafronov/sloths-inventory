from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("my/", views.my_items, name="my-items"),
    path("items/<int:item_id>/", views.item_history, name="item-history"),
]
