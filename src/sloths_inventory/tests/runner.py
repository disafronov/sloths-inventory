from django.test.runner import DiscoverRunner

class PytestTestRunner(DiscoverRunner):
    """Test runner that uses pytest."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 