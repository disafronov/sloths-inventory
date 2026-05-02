"""
Print EXPLAIN plans for inventory list page querysets.

Used to validate index choices and catch regressions when ORM fragments change.
See ``docs/inventory-list-query-profiling.md`` for how to run against PostgreSQL.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

from catalogs.models import Responsible
from inventory.models import build_my_items_page_data, build_previous_items_page_data


class Command(BaseCommand):
    """Emit EXPLAIN (optionally ANALYZE) for My items / Previously held querysets."""

    help = (
        "Print EXPLAIN for inventory list page querysets. "
        "PostgreSQL: EXPLAIN (ANALYZE, BUFFERS). Other backends: plain EXPLAIN."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--responsible-id",
            type=int,
            default=None,
            help=(
                "Primary key of catalogs.Responsible to scope querysets "
                "(default: first row)."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        rid = options["responsible_id"]
        if rid is not None:
            responsible = Responsible.objects.filter(pk=rid).first()
            if responsible is None:
                self.stderr.write(self.style.ERROR(f"No Responsible with pk={rid}."))
                return
        else:
            responsible = Responsible.objects.order_by("pk").first()
            if responsible is None:
                responsible = Responsible.objects.create(
                    last_name="Explain", first_name="Probe"
                )
                self.stdout.write(
                    self.style.WARNING(
                        "No Responsible rows; created a throwaway row for profiling."
                    )
                )

        analyze = connection.vendor == "postgresql"
        if not analyze:
            self.stderr.write(
                self.style.WARNING(
                    "Non-PostgreSQL backend: omitting ANALYZE/BUFFERS "
                    "(timing is not meaningful)."
                )
            )

        page_my = build_my_items_page_data(responsible, query="", list_kind="all")
        page_prev = build_previous_items_page_data(responsible, query="")

        sections: list[tuple[str, Any]] = [
            ("my_items.items", page_my.items),
            ("my_items.incoming_transfers", page_my.incoming_transfers),
            ("my_items.outgoing_transfers", page_my.outgoing_transfers),
            ("previous_items.items", page_prev.items),
            ("previous_items.incoming_transfers", page_prev.incoming_transfers),
            ("previous_items.outgoing_transfers", page_prev.outgoing_transfers),
        ]

        for label, qs in sections:
            self.stdout.write(self.style.HTTP_INFO(f"\n--- {label} ---\n"))
            if analyze:
                self.stdout.write(qs.explain(analyze=True, buffers=True))
            else:
                self.stdout.write(qs.explain())
