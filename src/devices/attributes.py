from django.utils.translation import gettext_lazy as _

from common.catalog_correction_window import CatalogCorrectionWindowMixin
from common.models import NamedModel


class Category(CatalogCorrectionWindowMixin, NamedModel):
    """
    Device category model.

    Used to classify devices by their purpose or type.
    """

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Device`` references this category."""

        if self._state.adding:
            return False
        from devices.models import Device

        return Device.objects.filter(category_id=self.pk).exists()


class Manufacturer(CatalogCorrectionWindowMixin, NamedModel):
    """
    Device manufacturer model.

    Stores information about hardware manufacturers.
    """

    class Meta:
        verbose_name = _("Manufacturer")
        verbose_name_plural = _("Manufacturers")

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Device`` references this manufacturer."""

        if self._state.adding:
            return False
        from devices.models import Device

        return Device.objects.filter(manufacturer_id=self.pk).exists()


class Model(CatalogCorrectionWindowMixin, NamedModel):
    """
    Device model.

    Represents a specific product model from a manufacturer.
    """

    class Meta:
        verbose_name = _("Model")
        verbose_name_plural = _("Models")

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Device`` references this model row."""

        if self._state.adding:
            return False
        from devices.models import Device

        return Device.objects.filter(model_id=self.pk).exists()


class Type(CatalogCorrectionWindowMixin, NamedModel):
    """
    Device type model.

    Used for additional device classification.
    """

    class Meta:
        verbose_name = _("Type")
        verbose_name_plural = _("Types")

    def is_catalog_reference_in_use(self) -> bool:
        """True when any ``Device`` references this type."""

        if self._state.adding:
            return False
        from devices.models import Device

        return Device.objects.filter(type_id=self.pk).exists()
