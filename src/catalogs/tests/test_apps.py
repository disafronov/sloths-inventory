from catalogs.apps import CatalogsConfig

def test_catalogs_config():
    config = CatalogsConfig('catalogs', 'catalogs')
    assert config.name == 'catalogs'
    assert config.verbose_name == 'Каталоги'
    assert config.default_auto_field == 'django.db.models.BigAutoField' 