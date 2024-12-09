from types import SimpleNamespace

config = SimpleNamespace(
    ip_address='192.168.0.114',
    tapo_ip_address="192.168.0.106", 
    max_export=5000,
    max_export_set=5400,
    min_battery_charge_for_water_heating=75,
    min_solar_output_for_water_heating=2500,
    min_minutes_before_deactivate_limit=30,
    min_minutes_activation_time_tapo=120,
    max_minutes_activation_time_tapo=200,
    min_minutes_between_gridexport_switch=5,
    check_for_electricity_price=True
)