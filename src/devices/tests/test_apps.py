from devices.apps import DevicesConfig

def test_devices_config():
    config = DevicesConfig('devices', 'devices')
    assert config.name == 'devices'
    assert config.verbose_name == 'Устройства'
    assert config.default_auto_field == 'django.db.models.BigAutoField' 