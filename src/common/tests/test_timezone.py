import pytest
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from common.timezone import TimezoneMiddleware, timezone_context


class TestTimezoneMiddleware:
    def setup_method(self):
        self.factory = RequestFactory()
        self.middleware = TimezoneMiddleware(lambda r: None)

    def test_no_cookie_deactivates_and_marks_undetected(self):
        request = self.factory.get("/")
        self.middleware(request)
        assert request.timezone_detected is False

    def test_valid_cookie_activates_and_marks_detected(self):
        request = self.factory.get("/", HTTP_COOKIE="timezone=Europe/Moscow")
        self.middleware(request)
        assert request.timezone_detected is True
        assert str(timezone.get_current_timezone()) == "Europe/Moscow"

    def test_percent_encoded_cookie_activates_and_marks_detected(self):
        request = self.factory.get("/", HTTP_COOKIE="timezone=Asia%2FYerevan")
        self.middleware(request)
        assert request.timezone_detected is True
        assert str(timezone.get_current_timezone()) == "Asia/Yerevan"

    def test_invalid_cookie_deactivates_and_marks_undetected(self):
        request = self.factory.get("/", HTTP_COOKIE="timezone=Not%2FA%2FTimezone")
        self.middleware(request)
        assert request.timezone_detected is False


class TestTimezoneContext:
    def setup_method(self):
        self.factory = RequestFactory()

    def test_returns_detected_true_when_set(self):
        request = self.factory.get("/")
        request.timezone_detected = True
        ctx = timezone_context(request)
        assert ctx["timezone_detected"] is True

    def test_returns_detected_false_when_missing(self):
        request = self.factory.get("/")
        ctx = timezone_context(request)
        assert ctx["timezone_detected"] is False

    def test_returns_server_timezone(self, settings):
        request = self.factory.get("/")
        settings.TIME_ZONE = "Asia/Tokyo"
        ctx = timezone_context(request)
        assert ctx["server_timezone"] == "Asia/Tokyo"


@pytest.mark.django_db
class TestTimezoneBanner:
    def test_banner_shown_without_cookie(self, client: Client, django_user_model):
        django_user_model.objects.create_user(
            username="u", password="pw", email="u@example.com"
        )
        client.login(username="u", password="pw")
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200
        assert (
            _("Your timezone could not be detected. Times are displayed in %(tz)s.")
            % {"tz": "UTC"}
            in response.content.decode()
        )

    def test_banner_hidden_with_valid_cookie(self, client: Client, django_user_model):
        django_user_model.objects.create_user(
            username="u2", password="pw", email="u2@example.com"
        )
        client.login(username="u2", password="pw")
        client.cookies["timezone"] = "Europe/Moscow"
        response = client.get(reverse("common:profile"))
        assert response.status_code == 200
        content = response.content.decode()
        for lang_tz in ["UTC", "Europe/Moscow"]:
            assert (
                _("Your timezone could not be detected. Times are displayed in %(tz)s.")
                % {"tz": lang_tz}
                not in content
            )
