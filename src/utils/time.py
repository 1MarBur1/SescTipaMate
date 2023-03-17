import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import wraps


TIME_ZONE = ZoneInfo("Asia/Yekaterinburg")


def current_local_time():
    return datetime.now(tz=TIME_ZONE)


def every(interval):
    def __task_decorator(task_func):

        @wraps(task_func)
        async def __decorated_task():
            while True:
                await asyncio.sleep(interval.total_seconds())
                await task_func()

        return __decorated_task
    return __task_decorator


def everyday(time_repr: str):
    try:
        time_repr = tuple(map(int, time_repr.split(":")))
        hour, minute, second = time_repr[0], time_repr[1], 0
        if len(time_repr) == 3:
            second = time_repr[2]
    except (ValueError, KeyError) as exc:
        logging.error("Time stamp was given in wrong format")
        raise exc

    def __task_decorator(task_func):
        @wraps(task_func)
        async def __decorated_task():
            while True:
                now = current_local_time()
                delay = ((hour * 3600 + minute * 60 + second) -
                         (now.hour * 3600 + now.minute * 60 + now.second)) % 86400
                await asyncio.sleep(delay)
                await task_func()
        return __decorated_task

    return __task_decorator
