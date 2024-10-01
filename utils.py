import goodwe
import asyncio

async def disable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 0)

async def enable_grid_limit(inverter: goodwe.Inverter):
    inverter.write_setting("grid_export", 1)

def run_async(func: function, *args):
    result = asyncio.run(func(*args))
    return result