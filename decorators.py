import functools
import traceback
from logger import LoggerCustom

def error_handler(func):
    """Decorator to catch and log initialization errors without crashing"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Get logger from self if available, otherwise create new one
            logger = getattr(args[0], 'logManager', None) or LoggerCustom()
            logger.log(f"Error in {func.__name__}: {str(e)}", level=40)
            logger.log(f"Traceback: {traceback.format_exc()}", level=40)
            return None
    return wrapper