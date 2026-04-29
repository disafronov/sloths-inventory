from catalogs.models import Responsible


def test_responsible_full_name_formatting() -> None:
    responsible = Responsible(
        last_name="Ivanov",
        first_name="Ivan",
        middle_name="Ivanovich",
    )

    assert str(responsible) == "Ivanov Ivan Ivanovich"
    assert responsible.get_full_name() == "Ivanov Ivan Ivanovich"


def test_responsible_full_name_without_middle_name() -> None:
    responsible = Responsible(
        last_name="Ivanov",
        first_name="Ivan",
        middle_name=None,
    )

    assert str(responsible) == "Ivanov Ivan"
