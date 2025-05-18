from inventory.apps import InventoryConfig

def test_inventory_config():
    config = InventoryConfig('inventory', 'inventory')
    assert config.name == 'inventory'
    assert config.verbose_name == 'Инвентарь'
    assert config.default_auto_field == 'django.db.models.BigAutoField' 