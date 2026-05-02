"""
HTTP-facing presentation helpers for inventory.

These functions format domain exceptions for HTML templates; they do not encode
inventory business rules (those live on models).
"""

from django.core.exceptions import ValidationError


def validation_error_user_message(exc: ValidationError) -> str:
    """
    Collapse a ValidationError into one human-readable string for HTML templates.

    A bare ``str(exc)`` is fine for a single lazy translation but becomes awkward
    when Django attaches multiple messages or a ``message_dict`` (field errors).
    """

    message_dict = getattr(exc, "message_dict", None)
    if message_dict:
        parts: list[str] = []
        for field, msgs in message_dict.items():
            for msg in msgs:
                parts.append(f"{field}: {msg}")
        return "; ".join(parts)
    messages = getattr(exc, "messages", None)
    if messages is not None and len(messages) > 0:
        return "; ".join(str(m) for m in messages)
    return str(exc)
