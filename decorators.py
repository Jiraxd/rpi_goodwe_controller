import functools
import traceback
from logger import LoggerCustom
import asyncio

def error_handler(func):
    """Decorator to catch and log errors without crashing"""
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)
        except Exception as e:
            # Get logger from self if available, otherwise create new one
            logger = getattr(self, 'logManager', None)
            if not logger:
                logger = LoggerCustom()
            logger.log(f"| CAUGHT BY ERROR HANDLER | Error in {func.__name__}: {str(e)}", level=40)
            logger.log(f"Traceback: {traceback.format_exc()}", level=40)
            return None
    return async_wrapper