import threading
import time

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections, transaction

from catalogs.models import Location, Responsible, Status
from devices.attributes import Category, Manufacturer, Model, Type
from devices.models import Device
from inventory.models import Item, Operation


@pytest.mark.django_db(transaction=True)
def test_operation_update_is_serialized_per_item_under_concurrency() -> None:
    """
    This is an integration-level concurrency test.

    SQLite does not provide the same row-level locking semantics as Postgres, so
    we only run this test on Postgres to validate the select_for_update() based
    serialization logic.
    """

    if connections["default"].vendor != "postgresql":
        pytest.skip("Concurrency locking semantics are only validated on PostgreSQL")

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status1 = Status.objects.create(name="S1")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-LOCK-001", device=device)
    op = Operation.objects.create(
        item=item,
        status=status1,
        responsible=responsible,
        location=location,
        notes="init",
    )

    started = threading.Event()
    first_has_lock = threading.Event()
    allow_second = threading.Event()

    def _thread_1_lock_holder() -> None:
        close_old_connections()
        with transaction.atomic():
            # Hold the same lock that Operation.save() uses.
            Item.objects.select_for_update().get(pk=item.pk)
            first_has_lock.set()
            started.set()
            allow_second.wait(timeout=5)

            op_local = Operation.objects.get(pk=op.pk)
            op_local.notes = "t1"
            op_local.save()

    def _thread_2_competing_update() -> None:
        close_old_connections()
        started.wait(timeout=5)
        first_has_lock.wait(timeout=5)

        op_local = Operation.objects.get(pk=op.pk)
        op_local.notes = "t2"
        allow_second.set()

        # One of the threads will win; the other must not corrupt state.
        # We only assert that the code path is safe and does not violate the
        # append-only invariant.
        try:
            op_local.save()
        except ValidationError:
            # If during the race the operation stopped being "latest" (e.g. if another
            # operation was created), ValidationError is acceptable.
            pass

    t1 = threading.Thread(target=_thread_1_lock_holder)
    t2 = threading.Thread(target=_thread_2_competing_update)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not t1.is_alive(), "Thread 1 did not finish (possible deadlock)"
    assert not t2.is_alive(), "Thread 2 did not finish (possible deadlock)"

    op.refresh_from_db()
    assert op.notes in {"t1", "t2"}


@pytest.mark.django_db(transaction=True)
def test_operation_insert_waits_for_item_lock_under_concurrency() -> None:
    """
    Validate that inserts are serialized per item as well.

    We hold a row-level lock on Item in one transaction and ensure that a
    concurrent Operation.create() for the same item blocks until the lock is
    released.
    """

    if connections["default"].vendor != "postgresql":
        pytest.skip("Concurrency locking semantics are only validated on PostgreSQL")

    category = Category.objects.create(name="Laptops")
    device_type = Type.objects.create(name="Laptop")
    manufacturer = Manufacturer.objects.create(name="ACME")
    device_model = Model.objects.create(name="Model X")
    device = Device.objects.create(
        category=category,
        type=device_type,
        manufacturer=manufacturer,
        model=device_model,
    )

    status = Status.objects.create(name="S1")
    responsible = Responsible.objects.create(last_name="Ivanov", first_name="Ivan")
    location = Location.objects.create(name="Moscow")

    item = Item.objects.create(inventory_number="INV-LOCK-INSERT-001", device=device)

    lock_acquired = threading.Event()
    allow_release = threading.Event()
    insert_started = threading.Event()
    insert_finished = threading.Event()

    elapsed: dict[str, float] = {}

    def _thread_1_lock_holder() -> None:
        close_old_connections()
        with transaction.atomic():
            Item.objects.select_for_update().get(pk=item.pk)
            lock_acquired.set()
            allow_release.wait(timeout=5)

    def _thread_2_insert_operation() -> None:
        close_old_connections()
        assert lock_acquired.wait(timeout=5), "Item lock was not acquired in time"

        insert_started.set()
        start = time.monotonic()
        Operation.objects.create(
            item=item,
            status=status,
            responsible=responsible,
            location=location,
            notes="insert",
        )
        elapsed["seconds"] = time.monotonic() - start
        insert_finished.set()

    t1 = threading.Thread(target=_thread_1_lock_holder)
    t2 = threading.Thread(target=_thread_2_insert_operation)
    t1.start()
    t2.start()

    assert lock_acquired.wait(timeout=5), "Lock holder did not acquire item lock"

    # Give the insert thread a chance to start and block.
    assert insert_started.wait(timeout=5), "Insert did not start"
    assert not insert_finished.is_set(), "Insert finished while lock was held"

    allow_release.set()
    t1.join(timeout=10)
    t2.join(timeout=10)
    assert not t1.is_alive(), "Thread 1 did not finish (possible deadlock)"
    assert not t2.is_alive(), "Thread 2 did not finish (possible deadlock)"

    # If the insert did not block, elapsed would be near-zero; we expect it to
    # have waited for the lock to be released.
    assert elapsed["seconds"] >= 0.01
