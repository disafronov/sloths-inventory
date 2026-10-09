from typing import Any, cast

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


class SerializedSaveMixin(models.Model):
    """
    Save with concurrency-safe validation.

    Takes a row lock inside a transaction, snapshots pre-save state for
    signals, then runs ``full_clean()`` so concurrent writes cannot race past
    ``clean()`` checks (correction windows, append-only rules).

    Subclasses override :meth:`_lock_rows_for_update` when serialization needs
    a different row (``Operation`` and ``PendingTransfer`` lock their ``Item``)
    and :meth:`_capture_pre_save_state` to feed ``post_save`` signal handlers.
    """

    class Meta:
        abstract = True

    def _lock_rows_for_update(self) -> None:
        """Take row locks serializing concurrent writes (runs in a transaction)."""

        if not self._state.adding:
            # ``type(self)`` is a concrete model class; mypy cannot derive
            # ``.objects`` from the abstract mixin base.
            concrete_model_cls = cast(Any, type(self))
            concrete_model_cls.objects.select_for_update().only("id").get(pk=self.pk)

    def _capture_pre_save_state(self) -> None:
        """Snapshot fields needed after save (e.g. for signals). No-op by default."""

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Persist after validation with row-level serialization."""

        with transaction.atomic():
            self._lock_rows_for_update()
            self._capture_pre_save_state()
            self.full_clean()
            super().save(*args, **kwargs)


class BaseModel(models.Model):
    """
    Base class for all models with common fields.

    Provides timestamps for creation/update and a free-form notes field.
    """

    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        abstract = True


class NamedModel(BaseModel):
    """
    Base class for models that have a `name` field.

    Extends `BaseModel` with a unique `name` and default ordering by name.
    """

    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
