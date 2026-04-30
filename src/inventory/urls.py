from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.my_items, name="my-items"),
    path("previous/", views.previous_items, name="previous-items"),
    path("transfers/", views.transfers, name="transfers"),
    path(
        "transfers/incoming/",
        views.incoming_transfers,
        name="incoming-transfers",
    ),
    path(
        "transfers/outgoing/",
        views.outgoing_transfers,
        name="outgoing-transfers",
    ),
    path("items/<int:item_id>/", views.item_history, name="item-history"),
    path(
        "items/<int:item_id>/change-location/",
        views.change_location,
        name="change-location",
    ),
    path(
        "items/<int:item_id>/transfer/",
        views.create_transfer,
        name="create-transfer",
    ),
    path(
        "transfers/<int:transfer_id>/accept/",
        views.accept_transfer,
        name="accept-transfer",
    ),
    path(
        "transfers/<int:transfer_id>/cancel/",
        views.cancel_transfer,
        name="cancel-transfer",
    ),
]
