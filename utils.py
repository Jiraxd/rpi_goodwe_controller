import goodwe

async def disable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 0)

async def enable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 1)