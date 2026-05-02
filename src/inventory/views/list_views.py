"""Inventory list views (my items, previously held)."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from catalogs.models import Responsible
from inventory.models import (
    build_my_items_page_data,
    build_previous_items_page_data,
    parse_my_items_list_kind,
)


@login_required
def my_items(request: HttpRequest) -> HttpResponse:
    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        return render(
            request,
            "inventory/my_items.html",
            {
                "responsible": None,
                "items": [],
                "incoming_transfers": [],
                "outgoing_transfers": [],
                "query": "",
                "list_kind": "all",
            },
        )

    query = request.GET.get("q", "")
    list_kind = parse_my_items_list_kind(request.GET.get("kind", ""))
    page = build_my_items_page_data(responsible, query=query, list_kind=list_kind)
    return render(
        request,
        "inventory/my_items.html",
        {
            "responsible": responsible,
            "items": page.items,
            "query": query,
            "list_kind": list_kind,
            "incoming_transfers": page.incoming_transfers,
            "outgoing_transfers": page.outgoing_transfers,
        },
    )


@login_required
def previous_items(request: HttpRequest) -> HttpResponse:
    responsible = Responsible.linked_profile_for_user(request.user)
    if responsible is None:
        return render(
            request,
            "inventory/previous_items.html",
            {
                "responsible": None,
                "items": [],
                "incoming_transfers": [],
                "outgoing_transfers": [],
                "query": "",
            },
        )

    query = request.GET.get("q", "")
    page = build_previous_items_page_data(responsible, query=query)
    return render(
        request,
        "inventory/previous_items.html",
        {
            "responsible": responsible,
            "items": page.items,
            "query": query,
            "incoming_transfers": page.incoming_transfers,
            "outgoing_transfers": page.outgoing_transfers,
        },
    )
