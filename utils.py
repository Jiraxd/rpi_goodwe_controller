import goodwe

async def disable_grid_export(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 0)

async def enable_grid_export(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 1)

async def set_grid_limit(inverter: goodwe.Inverter, limit):
    inverter.write_setting("grid_export_limit", limit)
