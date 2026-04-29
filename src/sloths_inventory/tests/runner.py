from django.test.runner import DiscoverRunner


class PytestTestRunner(DiscoverRunner):
    """
    Stub runner for `manage.py test`.

    This project runs tests via pytest (see `make test` / `make all`). Django's
    test runner is intentionally disabled to avoid divergent test execution
    paths and confusing results.
    """

    def run_tests(  # type: ignore[override]
        self, _test_labels, _extra_tests=None, **_kwargs
    ):
        raise SystemExit(
            "Django test runner is disabled in this project.\n"
            "Run tests with: `make test` (or `make all`).\n"
            "If you need coverage: `make test-coverage`.\n"
        )
