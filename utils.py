import goodwe
from logger import LoggerCustom
from config import config

async def disable_grid_export(inverter: goodwe.Inverter, logManager : LoggerCustom):
    logManager.log("stopping export")
    return
    limit = await inverter.read_setting("grid_export_limit")
    if(limit != 0):
        inverter.write_setting("grid_export_limit", 0)
    enabled = await inverter.read_setting("grid_export")
    if(enabled != 1):
        inverter.write_setting("grid_export", 1)

async def enable_grid_export(inverter: goodwe.Inverter, logManager : LoggerCustom):
    logManager.log("starting export")
    return
    limit = await inverter.read_setting("grid_export_limit")
    if(limit != config.max_export_set):
        inverter.write_setting("grid_export_limit", config.max_export_set)
    
async def disable_grid_limit(inverter: goodwe.Inverter, logManager : LoggerCustom):
    logManager.log("disabling limit")
    return
    
    inverter.write_setting("grid_export", 0)

async def enable_grid_limit(inverter: goodwe.Inverter, logManager : LoggerCustom):
    logManager.log("enabling limit")
    return
    limit = await inverter.read_setting("grid_export_limit")
    if(limit != config.max_export_set):
        inverter.write_setting("grid_export_limit", config.max_export_set)
    enabled = await inverter.read_setting("grid_export")
    if(enabled != 1):
        inverter.write_setting("grid_export", 1)

