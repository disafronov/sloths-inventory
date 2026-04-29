from typing import Any, Optional, overload

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from catalogs.models import Location, Responsible, Status
from common.models import BaseModel
from devices.models import Device


class Item(BaseModel):
    inventory_number = models.CharField(
        max_length=50, unique=True, verbose_name=_("Inventory number")
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, verbose_name=_("Device")
    )
    serial_number = models.CharField(
        max_length=50, blank=True, verbose_name=_("Serial number")
    )

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        ordering = ["inventory_number"]

    def __str__(self) -> str:
        return self.get_display_name()

    def get_display_name(self) -> str:
        return f"{self.inventory_number} - {self.device}"

    def clean(self) -> None:
        """Валидация модели."""
        if not self.inventory_number:
            raise ValidationError(
                {"inventory_number": _("Inventory number cannot be empty")}
            )

    @property
    def current_operation(self) -> Optional["Operation"]:
        return self.operation_set.order_by("-created_at").first()

    class CurrentOperationValue:
        def __init__(self, attr_name: str) -> None:
            self.attr_name = attr_name

        @overload
        def __get__(
            self, instance: None, owner: type["Item"]
        ) -> "Item.CurrentOperationValue": ...

        @overload
        def __get__(self, instance: "Item", owner: type["Item"]) -> Optional[str]: ...

        def __get__(self, instance: Optional["Item"], owner: type["Item"]) -> Any:
            if instance is None:
                return self
            operation = instance.current_operation
            if not operation:
                return None

            value = getattr(operation, self.attr_name, None)
            if value and hasattr(value, "name"):
                return value.name
            return value

    current_status = CurrentOperationValue("status")
    current_location = CurrentOperationValue("location")
    current_responsible = CurrentOperationValue("responsible")


class Operation(BaseModel):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, verbose_name=_("Item"))
    status = models.ForeignKey(
        Status, on_delete=models.PROTECT, verbose_name=_("Status")
    )
    responsible = models.ForeignKey(
        Responsible, on_delete=models.PROTECT, verbose_name=_("Responsible")
    )
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, verbose_name=_("Location")
    )

    class Meta:
        verbose_name = _("Operation")
        verbose_name_plural = _("Operations")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.item} - {self.status} ({self.location})"

    def get_responsible_display(self) -> str:
        """Возвращает строковое представление ответственного."""
        return str(self.responsible)
