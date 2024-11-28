import goodwe
from main import logManager

async def disable_grid_export(inverter: goodwe.Inverter):
    logManager.log("stopping export")
    return
    inverter.write_setting("grid_export", 0)

async def enable_grid_export(inverter: goodwe.Inverter):
    logManager.log("starting export")
    return
    inverter.write_setting("grid_export", 1)

async def set_grid_limit(inverter: goodwe.Inverter, limit):
    logManager.log(f"changing limit: {limit}")
    return
    inverter.write_setting("grid_export_limit", limit)
