import functools
import traceback
from loggerCustom import LoggerCustom
import asyncio

def error_handler(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        instance = args[0] if args else None
        
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except Exception as e:
            # Get logger from instance or create new one
            logger = getattr(instance, 'logManager', None) 
            if not logger:
                logger = LoggerCustom()
                
            logger.log(f"| CAUGHT BY ERROR HANDLER | Error in {func.__name__}: {str(e)}", level=40)
            logger.log(f"Traceback: {traceback.format_exc()}", level=40)
            return None
            
    return async_wrapper